import html
import itertools
import re
import sys
import time
from collections import deque
from functools import reduce
from multiprocessing.pool import ThreadPool
from pathlib import Path
from typing import NamedTuple
from zipfile import ZIP_DEFLATED, ZipFile

import browser_cookie3
import requests
from pyquery import PyQuery

BOOK_JSON_URL = "https://learning.oreilly.com/api/v2/epubs/{0}/"
LIMIT_FORMATTED_URL = "{0}?limit={1}"
FILE_LIST_LIMIT_FORMATTED_URL = "https://learning.oreilly.com/api/v2/epubs/urn:orm:book:{0}/files/?limit={2}&offset={1}"

XML_CONTAINER = {
    "kind": "other_asset",
    "full_path": "container.xml",
    "filename": "container.xml",
    "filename_ext": ".xml",
}
XML_CONTENTS = '<?xml version="1.0" encoding="UTF-8"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="{0}" media-type="{1}"/></rootfiles></container>'

escape_dirname = lambda x: re.compile(r"[^a-zA-Z0-9_,. ]").sub("_", x)  # noqa: E731
fetch_content_buffer = lambda url: CACHE.get(url).content  # noqa: E731
fetch_text = lambda url: CACHE.get(url).text  # noqa: E731

OUT_PATH = Path("out/")
OUT_PATH.mkdir(exist_ok=True)

KINDLE_HTML = (
    "#sbo-rt-content *{{word-wrap:break-word!important;"
    "word-break:break-word!important;}}#sbo-rt-content table,#sbo-rt-content pre"
    "{{overflow-x:unset!important;overflow:unset!important;"
    "overflow-y:unset!important;white-space:pre-wrap!important;}}"
)


# sourced from https://github.com/azec-pdx/safaribooks/blob/master/retrieve_cookies.py, modified to account for different browsers.
def get_oreilly_cookies():
    domains = ["learning.oreilly.com", "www.oreilly.com", "oreilly.com", ".oreilly.com"]

    cookies = {}
    browser = None

    try:
        try:
            _ = browser_cookie3.chrome()
            browser = "chrome"
        except browser_cookie3.BrowserCookieError:
            print("failed to locate chrome cookies")
            _ = browser_cookie3.firefox()
            browser = "firefox"
    except browser_cookie3.BrowserCookieError:
        print("failed to locate firefox cookies")
        _ = browser_cookie3.chromium()
        browser = "chromium"

    def scrape_cookie(domain: str):
        match browser:
            case "chrome":
                cj = browser_cookie3.chrome(domain_name=domain)
            case "firefox":
                cj = browser_cookie3.firefox(domain_name=domain)
            case "chromium":
                cj = browser_cookie3.chromium(domain_name=domain)

        list(map(lambda c: cookies.update({c.name: c.value}), cj))

    list(map(scrape_cookie, domains))
    return cookies


CACHE = requests.Session()
CACHE.cookies.update(get_oreilly_cookies())


format_chapter = lambda book_json, formatted_stylesheets, chapter_content: (  # noqa: E731
    '<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE html><html xml:lang="'
    + book_json["language"]
    + '" xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops"><head><title>'
    + html.escape((book_json["title"]))
    + "</title>"
    + "".join(formatted_stylesheets)
    + '</head><body><div id="book-content"><div id="sbo-rt-content">'
    + chapter_content
    + "</div></body></html>"
)


class ContentBuffer(NamedTuple):
    file_path: str
    buffer: bytes
    level: int


class OreillyEpubParser:
    def __init__(self, args):
        self.id, self.args, self.relative_stylesheets = args.bookid, args, []
        self.book_info_json = self.get_book_json()
        self.file_list = self.get_file_list()
        self.file_contents = deque()
        self.is_pdf_converted = False

        print(f"Downloading {self.id}")

    def get_book_json(self):
        while True:
            response = requests.get(BOOK_JSON_URL.format(self.id))

            if response.status_code == 200:
                break

            print("request failed, retrying")

        return response.json()

    def parse_and_replace_html(self, x, info: dict):
        direct_file_path_denominator = reduce(
            lambda a, y: a + "../" if y == "/" else a, info["full_path"], initial=""
        )

        d = PyQuery(
            x.replace("/api/v2/epubs/urn:orm:book:{0}/files/".format(self.id), "")
        )

        if d("h1").text() == "Access Denied":
            print(
                "Oreilly has blacklisted your IP, wait a little or swap IPs before trying again."
            )
            sys.exit()

        d.remove("script")
        d.remove("link")

        if self.is_pdf_converted:
            list(
                map(
                    lambda x: x.append("</span>"),
                    itertools.chain(d("div").find("span").items()),
                )
            )
            list(
                map(
                    lambda x: x.append("</div>"),
                    itertools.chain(d("div").items()),
                )
            )

        combined_tags = itertools.chain(d("img").items(), d("image"))

        def handle_tags(x):
            src = x.attr("src")
            href = x.attr("href")

            if src:
                x.attr("src", direct_file_path_denominator + src)

            if href:
                x.attr("href", direct_file_path_denominator + href)

        list(map(handle_tags, combined_tags))

        html = str(d.html())

        formatted_stylesheets = list(
            map(
                lambda x: (
                    f'<link rel="stylesheet" type="text/css" href="{direct_file_path_denominator}{x}"/>'
                ),
                self.relative_stylesheets,
            )
        )

        if d("#sbo-rt-content").eq(0):
            return format_chapter(
                self.book_info_json, formatted_stylesheets, html
            ).encode()

        return html.encode()

    def determine_relative_epub_file_path(self, filename, full_path):
        if filename.startswith("container"):
            return "META-INF/{0}".format(full_path)
        elif filename.startswith("mimetype"):
            return full_path

        return "OEBPS/{0}".format(full_path)

    def get_file_list(self):
        file_list = self.book_info_json["files"]

        while True:
            response = requests.get(LIMIT_FORMATTED_URL.format(file_list, 1))

            if response.status_code == 200:
                break

            print("request failed, retrying")

        out = response.json()
        file_count = out["count"]

        if file_count < 1000:
            files = requests.get(
                FILE_LIST_LIMIT_FORMATTED_URL.format(
                    self.book_info_json["identifier"], 0, file_count
                )
            ).json()["results"]
            return files

        files = list(
            itertools.chain.from_iterable(
                map(
                    lambda i: requests.get(
                        FILE_LIST_LIMIT_FORMATTED_URL.format(
                            self.book_info_json["identifier"], i, 1000
                        )
                    ).json()["results"],
                    list(range(0, file_count, 1000)),
                )
            )
        )
        return files

    def collect_stylesheets(self):
        response = requests.get(
            LIMIT_FORMATTED_URL.format(self.book_info_json["spine"], 2)
        ).json()
        results = response["results"][len(response["results"]) - 1]["url"]
        stylesheets = requests.get(results).json()["related_assets"]["stylesheets"]
        list(
            map(
                lambda sheet: self.relative_stylesheets.append(
                    sheet.replace(self.book_info_json["files"], "")
                ),
                stylesheets,
            )
        )

    def handle_xml(self, file):
        type = file["media_type"]

        if type == "application/oebps-package+xml":
            self.file_contents.append(
                ContentBuffer(
                    self.determine_relative_epub_file_path(
                        XML_CONTAINER["filename"], XML_CONTAINER["full_path"]
                    ),
                    XML_CONTENTS.format(
                        "OEBPS/" + file["full_path"], file["media_type"]
                    ).encode(),
                    9,
                )
            )
            return fetch_text(file["url"]).encode()
        elif type == "application/x-dtbncx+xml":
            content = fetch_content_buffer(file["url"])

            if not content.endswith(b'"UTF-8"?>'):
                return content

            return b'<?xml version="1.0" encoding="UTF-8"?>' + content

        return fetch_content_buffer(file["url"])

    def handle_file(self, file: dict):
        if self.args.sleep:
            time.sleep(3)

        if self.args.verbose:
            print(file)

        if file["kind"] == "chapter":
            return self.parse_and_replace_html(
                fetch_content_buffer(file["url"]).decode(), file
            )
        elif file["kind"] == "other_asset":
            return self.handle_xml(file)

        return fetch_content_buffer(file["url"])

    def zip_epub_contents(self, book_contents):
        with ZipFile(
            (
                OUT_PATH
                / ("{0}.epub".format(escape_dirname(self.book_info_json["title"])))
            ),
            "w",
            compression=ZIP_DEFLATED,
        ) as handle:
            list(
                map(
                    lambda x: handle.writestr(
                        x.file_path, x.buffer, compresslevel=x.level
                    ),
                    book_contents,
                )
            )
            handle.close()

        print(f"Finished {self.id}")

    def setup_file_contents(self):
        self.collect_stylesheets()

        if list(filter(lambda x: "pdf2htmlEX" in x["filename"], self.file_list)):
            self.is_pdf_converted = True
            print("EPUB is PDF converted. DO NOT USE CALIBRE'S EBOOK-CONVERT!")
            self.file_list = list(
                itertools.filterfalse(
                    lambda x: re.compile("^pdf2htmlEX|^[A-Za-z]+.js$").match(
                        x["filename"]
                    ),
                    self.file_list,
                )
            )

        threads = ThreadPool(3)
        threads.map(
            lambda x: self.file_contents.append(
                ContentBuffer(
                    self.determine_relative_epub_file_path(
                        x["filename"], x["full_path"]
                    ),
                    self.handle_file(x),
                    0 if "image" == x["kind"] else 9,
                )
            ),
            self.file_list,
        )
        threads.close()

        self.file_contents.append(
            ContentBuffer(
                self.determine_relative_epub_file_path("mimetype", "mimetype"),
                b"application/epub+zip",
                0,
            )
        )

        return self.file_contents
