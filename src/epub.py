import itertools
import random
import re
import sys
import time
from argparse import Namespace
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from functools import reduce
from zipfile import ZIP_DEFLATED, ZipFile

from lxml.html import HtmlElement
from pyquery import PyQuery

from constants import (
    BOOK_JSON_URL,
    FILE_LIST_LIMIT_FORMATTED_URL,
    KINDLE_CSS,
    LIMIT_FORMATTED_URL,
    OUT_PATH,
    XML_CONTENTS,
)
from utils import ContentBuffer, escape_dirname, fetch, format_chapter


class OreillyEpubParser:
    def __init__(self, args: Namespace):
        self.args: Namespace = args
        self.id: str = self.args.bookid
        self.relative_stylesheets: list = []
        self.book_info_json: dict = self.get_book_json()
        self.file_list: list = self.get_file_list()
        self.file_contents: deque = deque()
        self.is_pdf_converted: bool = False

        print(f"Downloading {self.book_info_json['title']}")

    def get_book_json(self) -> dict:
        return fetch(BOOK_JSON_URL.format(self.id)).json()

    def parse_and_replace_html(self, chapter_html: str, info: dict) -> bytes:
        direct_file_path_denominator = reduce(
            lambda a, y: a + "../" if y == "/" else a, info["full_path"], initial=""
        )

        d = PyQuery(
            chapter_html.replace(
                "/api/v2/epubs/urn:orm:book:{0}/files/".format(self.id), ""
            )
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
                    lambda x: x.append("</a>"),
                    itertools.chain(d("div").find("a").items()),
                )
            )
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

        images = itertools.chain(d("img").items(), d("image").items())

        def handle_images(x):
            for elem in ("src", "href"):
                attr = x.attr(elem) if not isinstance(x, HtmlElement) else x.get(elem)

                if attr:
                    x.attr(elem, direct_file_path_denominator + attr) if not isinstance(
                        x, HtmlElement
                    ) else x.set(elem, direct_file_path_denominator + attr)

        if info["filename"] == "titlepage.xhtml":
            cover_href = d("image").attr("href")
            html = str(d.html()).replace(
                f'href="{cover_href}"',
                f'href="{direct_file_path_denominator}{cover_href}"',
            )
        else:
            list(map(handle_images, images))
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

    def get_file_list(self) -> list:
        file_count = fetch(
            LIMIT_FORMATTED_URL.format(self.book_info_json["files"], 1)
        ).json()["count"]

        if file_count < 1000:
            files = fetch(
                FILE_LIST_LIMIT_FORMATTED_URL.format(
                    self.book_info_json["identifier"], 0, file_count
                )
            ).json()["results"]
            return files

        files = list(
            itertools.chain.from_iterable(
                map(
                    lambda i: fetch(
                        FILE_LIST_LIMIT_FORMATTED_URL.format(
                            self.book_info_json["identifier"], i, 1000
                        )
                    ).json()["results"],
                    list(range(0, file_count, 1000)),
                )
            )
        )
        return files

    def collect_stylesheets(self) -> None:
        res = fetch(LIMIT_FORMATTED_URL.format(self.book_info_json["spine"], 2)).json()
        results = res["results"][len(res["results"]) - 1]["url"]
        list(
            map(
                lambda sheet: self.relative_stylesheets.append(
                    sheet.replace(self.book_info_json["files"], "")
                ),
                fetch(results).json()["related_assets"]["stylesheets"],
            )
        )

        if self.args.kindle:
            self.file_contents.append(
                ContentBuffer(
                    "OEBPS/kindle.css",
                    KINDLE_CSS,
                    9,
                )
            )
            self.relative_stylesheets.append("kindle.css")

    def handle_xml(self, file: dict) -> bytes:
        type = file["media_type"]

        if type == "application/oebps-package+xml":
            self.file_contents.append(
                ContentBuffer(
                    "META-INF/container.xml",
                    XML_CONTENTS.format(
                        "OEBPS/" + file["full_path"], file["media_type"]
                    ).encode(),
                    9,
                )
            )
            return fetch(file["url"]).text.encode()
        elif type == "application/x-dtbncx+xml":
            content = fetch(file["url"]).content

            if not content.endswith(b'"UTF-8"?>'):
                return content

            return b'<?xml version="1.0" encoding="UTF-8"?>' + content

        return fetch(file["url"]).content

    def handle_file(self, file: dict) -> bytes:
        if self.args.sleep:
            time.sleep(random.randrange(0, 3))

        if self.args.verbose:
            print(file)

        if file["kind"] == "chapter":
            return self.parse_and_replace_html(
                fetch(file["url"]).content.decode(), file
            )
        elif file["kind"] == "other_asset":
            return self.handle_xml(file)

        return fetch(file["url"]).content

    def zip_epub_contents(self, book_contents: deque) -> None:
        with ZipFile(
            (
                OUT_PATH
                / "{0}.epub".format(escape_dirname(self.book_info_json["title"]))
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

        print(f"Finished {self.book_info_json['title']}")

    def setup_file_contents(self) -> deque:
        self.collect_stylesheets()

        if list(filter(lambda x: "pdf2htmlEX" in x["filename"], self.file_list)):
            self.is_pdf_converted = True
            print("EPUB is PDF converted. DO NOT USE CALIBRE'S EBOOK-CONVERT!")
            self.file_list = list(
                itertools.filterfalse(
                    lambda x: re.compile("^pdf2htmlEX").match(
                        x["filename"]
                    ),
                    self.file_list,
                )
            )

        with ThreadPoolExecutor(3) as threads:
            [threads.submit(self.push_buffer(file)) for file in self.file_list]
            threads.shutdown(wait=True)

        self.file_contents.append(
            ContentBuffer(
                "mimetype",
                b"application/epub+zip",
                0,
            )
        )

        return self.file_contents

    def push_buffer(self, x: dict):
        buf = self.handle_file(x)
        
        self.file_contents.append(
            ContentBuffer(
                f"OEBPS/{x['full_path']}",
                buf,
                0 if "image" == x["kind"] else 9,
            )
        )
