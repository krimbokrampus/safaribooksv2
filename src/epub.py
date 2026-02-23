import asyncio
import html
import itertools
import re
import time
from functools import reduce
from multiprocessing.pool import ThreadPool
from typing import NamedTuple
from zipfile import ZIP_DEFLATED, ZipFile

import browser_cookie3
import requests
from pyquery import PyQuery

TEST_ID = 9781000925968
TEST_ID_2 = 9781592538218
BOOK_JSON_URL = "https://learning.oreilly.com/api/v2/epubs/{0}/"

LIMIT_FORMATTED_URL = "{0}?limit={1}"
FILE_LIST_LIMIT_FORMATTED_URL = "https://learning.oreilly.com/api/v2/epubs/urn:orm:book:{0}/files/?limit=1000&offset={1}"

SHOULD_SLEEP = False
SLEEP_TIME = 0

if SHOULD_SLEEP:
    SLEEP_TIME = 5

html_dec = lambda x: html.escape(x)  # noqa: E731
fetch_content_buffer = lambda url: CACHE.get(url).content  # noqa: E731
fetch_text = lambda url: CACHE.get(url).text  # noqa: E731


# taken from https://github.com/lorenzodifuccia/safaribooks/blob/master/safaribooks.py
def escape_dirname(dirname, clean_space=False):
    for ch in [
        "~",
        "#",
        "%",
        "&",
        "*",
        "{",
        "}",
        "\\",
        "<",
        ">",
        "?",
        "/",
        "`",
        "'",
        '"',
        "|",
        "+",
        ":",
    ]:
        if ch in dirname:
            dirname = dirname.replace(ch, "_")

    return dirname if not clean_space else dirname.replace(" ", "")


# taken from https://github.com/azec-pdx/safaribooks/blob/master/retrieve_cookies.py
def get_oreilly_cookies():
    domains = [
        "learning-oreilly-com.ezproxy.spl.org",
        "www-oreilly-com.ezproxy.spl.org",
        ".ezproxy.spl.org",
        ".spl.org",
        ".www.spl.org",
        "learning.oreilly.com",
        "www.oreilly.com",
        "oreilly.com",
        ".oreilly.com",
        "api.oreilly.com",
    ]
    cookies = {}
    for d in domains:
        cj = browser_cookie3.chromium(domain_name=d)
        for c in cj:
            cookies[c.name] = c.value
    return cookies


CACHE = requests.Session()
CACHE.cookies.update(get_oreilly_cookies())

format_chapter = lambda e, t, a, j: (  # noqa: E731
    '<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE html><html xml:lang="'
    + e["language"]
    + '" lang="'
    + e["language"]
    + '" xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops"><head><title>'
    + html_dec(e["title"])
    + "</title>"
    + "".join(a)
    + '</head><body><div id="book-content"><div id="sbo-rt-content">'
    + j
    + "</div></body></html>"
)


class ContentBuffer(NamedTuple):
    filepath: str
    buffer: bytes
    level: int


class OreillyEpubParser:
    def __init__(self, id, push_func):
        self.id, self.push_func, self.relative_stylesheets = id, push_func, []
        self.book_info_json = asyncio.run(self.get_book_json())
        self.file_list = asyncio.run(self.get_file_list())

    def sub_script(self, html: str):
        regex = re.compile(
            r"<script.*></script>|<link.*/>|<link.*>",
            flags=(re.IGNORECASE | re.MULTILINE | re.DOTALL),
        )
        return regex.sub("", html)

    async def get_book_json(self):
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

        html = x.replace("/api/v2/epubs/urn:orm:book:{0}/files/".format(self.id), "")
        html = self.sub_script(html)

        d = PyQuery(html)

        combined_tags = itertools.chain(d("img").items(), d("image").items())
        for tag in combined_tags:
            tag_html = str(tag)
            src = tag.attr("src")
            href = tag.attr("href")

            if src:
                tag.attr("src", direct_file_path_denominator + src)

            if href:
                tag.attr("href", direct_file_path_denominator + href)

            if ">" not in tag_html:
                tag_html = tag_html.replace(">", "/>")
                tag.replace_with(tag_html)

        regex = re.compile(
            r"(?:<(?:br|col|hr)(?!group)(?:[^>]?|[^>]+))(?<!/)>",
            flags=(re.IGNORECASE | re.MULTILINE | re.DOTALL),
        )
        html = str(d.html())

        matches = regex.findall(html)
        test_var1 = None
        test_var2 = None

        for match in matches:
            test_var1 = html
            # span tag?
            test_var2 = match[0]

            if "div" in test_var2:
                html = test_var1.replace(
                    test_var2, test_var2.replace("div>", "div></div>")
                )

            if "span" in test_var2:
                html = test_var1.replace(
                    test_var2, test_var2.replace("span>", "span></span>")
                )

        items = list(
            map(
                lambda x: (
                    f'<link rel="stylesheet" type="text/css" href="{direct_file_path_denominator}{x}"/>'
                ),
                self.relative_stylesheets,
            )
        )
        if d("#sbo-rt-content").eq(0):
            return bytes(
                format_chapter(
                    self.book_info_json, direct_file_path_denominator, items, html
                ),
                encoding="utf-8",
            )

        return bytes(html, encoding="utf-8")

    @staticmethod
    def determine_relative_epub_file_path(filename, filename_ext, full_path):
        match filename_ext:
            case ".xml":
                if filename.startswith("container") or filename.startswith(
                    "com.apple.ibooks.display-options"
                ):
                    return "META-INF/{0}".format(full_path)

                return "OEBPS/{0}".format(full_path)
            case "":
                return full_path
            case _:
                return "OEBPS/{0}".format(full_path)

    async def get_file_list(self):
        file_list = self.book_info_json["files"]

        while True:
            response = requests.get(LIMIT_FORMATTED_URL.format(file_list, 1))

            if response.status_code == 200:
                break

            print("request failed, retrying")

        out = response.json()
        file_count = out["count"]

        if file_count < 1000:
            return requests.get(
                LIMIT_FORMATTED_URL.format(file_list, file_count)
            ).json()["results"]

        # threads = ThreadPool()
        files = itertools.chain.from_iterable(
            list(
                map(
                    lambda i: self.request_file,
                    list(range(0, file_count, 1000)),
                )
            )
        )
        # threads.close()

        return {"count": file_count, "results": files}

    def request_file(self, x):
        if SHOULD_SLEEP:
            time.sleep(SLEEP_TIME)
        return requests.get(
            FILE_LIST_LIMIT_FORMATTED_URL.format(self.book_info_json["identifier"], x)
        ).json()["results"]

    def collect_stylesheets(self, x: dict):
        response = requests.get(LIMIT_FORMATTED_URL.format(x["spine"], 2)).json()
        results = response["results"][len(response["results"]) - 1]["url"]
        stylesheets = requests.get(results).json()["related_assets"]["stylesheets"]
        list(
            map(
                lambda i: self.relative_stylesheets.append(
                    stylesheets[i].replace(x["files"], "")
                ),
                range(0, len(stylesheets)),
            )
        )

    def handle_file(self, file: dict):
        match file["kind"]:
            case "chapter":
                return self.parse_and_replace_html(
                    fetch_content_buffer(file["url"]).decode(), file
                )
            case "other_asset":
                match file["media_type"]:
                    case "application/oebps-package+xml":
                        container = {
                            "kind": "other_asset",
                            "full_path": "container.xml",
                            "filename": "container.xml",
                            "filename_ext": ".xml",
                        }
                        contents: bytes = bytes(
                            '<?xml version="1.0" encoding="UTF-8"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="{0}" media-type="{1}"/></rootfiles></container>'.format(
                                "OEBPS/" + file["full_path"], file["media_type"]
                            ),
                            encoding="utf-8",
                        )

                        self.push_func(
                            {
                                "file": container,
                                "fileContents": contents,
                            }
                        )
                        return fetch_text(file["url"])  # ?
                    case "application/x-dtbncx+xml":
                        content = fetch_text(file["url"])
                        if content.endswith("?xml version="):
                            return '<?xml version="1.0" encoding="UTF-8"?>' + content
                        return content
                    case _:
                        return fetch_content_buffer(file["url"])
            case _:
                return fetch_content_buffer(file["url"])

    def zip_epub_contents(self, mapped_files):
        with ZipFile(
            "out/{0}.epub".format(escape_dirname(self.book_info_json["title"])),
            "w",
            compression=ZIP_DEFLATED,
        ) as handle:
            list(
                map(
                    lambda x: handle.writestr(
                        x.filepath, x.buffer, compresslevel=x.level
                    ),
                    mapped_files,
                )
            )
            handle.close()

    async def get_file_contents(self):
        self.collect_stylesheets(self.book_info_json)

        threads = ThreadPool(10)
        threads.map(
            lambda e: self.push_func(
                {
                    "file": e,
                    "fileContents": self.handle_file(e)
                    if isinstance(self.handle_file(e), bytes)
                    else self.handle_file(e).encode(),
                }
            ),
            self.file_list,
        )
        threads.close()

        self.push_func(
            {
                "file": {
                    "kind": "other_asset",
                    "full_path": "mimetype",
                    "filename": "mimetype",
                    "filename_ext": "",
                },
                "fileContents": bytes("application/epub+zip", encoding="utf-8"),
            }
        )
