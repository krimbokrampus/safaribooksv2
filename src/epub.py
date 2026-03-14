import gc
import itertools
import json
import math
import random
import re
import shutil
import sys
import time
from argparse import Namespace
from collections import deque
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from functools import reduce
from typing import Optional
from zipfile import ZIP_DEFLATED, ZipFile

import requests
from lxml.html import HtmlElement
from pyquery import PyQuery

from constants import (
    BOOK_JSON_URL,
    FILE_LIST_LIMIT_FORMATTED_URL,
    KINDLE_CSS,
    LIMIT_FORMATTED_URL,
    OUT_DIR,
    # PBCTX_MANAGER,
    XML_CONTENTS,
)
from utils import FileData, escape_dirname, format_chapter, get_oreilly_cookies

ARGS: Optional[Namespace] = None


class OreillyEpubParser:
    def __init__(self, iden: str):
        self.id: str = iden
        self.cache: requests.Session = requests.Session()
        self.relative_stylesheets: list = []
        self.book_info_json: dict = self.get_book_json()
        self.title = self.book_info_json["title"]
        self.file_list: list = self.get_file_list()
        # self.prog_bar = PBCTX_MANAGER.counter(
        #     total=len(self.file_list), desc=self.title, unit="files"
        # )
        self.file_contents: deque[FileData] = deque()
        self.is_pdf_converted: bool = False

        if ARGS:
            self.args: Namespace = ARGS

        self.cache.cookies.update(
            get_oreilly_cookies(self.args.browsers)
            if not self.args.cookie_file
            else json.load(self.args.cookie_file.open())
        )

        self.files_out = OUT_DIR / iden
        self.files_out.mkdir(exist_ok=True)

    def get_book_json(self) -> dict:
        return self._fetch_result(BOOK_JSON_URL.format(self.id)).json()

    def _parse_and_replace_html(self, chapter_html: str, info: dict) -> bytes:
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
        file_count = self._fetch_result(
            LIMIT_FORMATTED_URL.format(self.book_info_json["files"], 1)
        ).json()["count"]

        if file_count < 1000:
            files = self._fetch_result(
                FILE_LIST_LIMIT_FORMATTED_URL.format(
                    self.book_info_json["identifier"], 0, file_count
                )
            ).json()["results"]
            return files

        files = list(
            itertools.chain.from_iterable(
                map(
                    lambda i: self._fetch_result(
                        FILE_LIST_LIMIT_FORMATTED_URL.format(
                            self.book_info_json["identifier"], i, 1000
                        )
                    ).json()["results"],
                    list(range(0, file_count, 1000)),
                )
            )
        )
        return files

    def _collect_stylesheets(self) -> None:
        res = self._fetch_result(
            LIMIT_FORMATTED_URL.format(self.book_info_json["spine"], 2)
        ).json()
        results = res["results"][len(res["results"]) - 1]["url"]
        list(
            map(
                lambda sheet: self.relative_stylesheets.append(
                    sheet.replace(self.book_info_json["files"], "")
                ),
                self._fetch_result(results).json()["related_assets"]["stylesheets"],
            )
        )

        if self.args.kindle:
            (self.files_out / "OEBPS/kindle.css").write_bytes(KINDLE_CSS)
            self.file_contents.append(FileData("OEBPS/kindle.css", 9))
            self.relative_stylesheets.append("kindle.css")

    def _handle_xml(self, file: dict, buf: requests.Response) -> bytes:
        type = file["media_type"]

        if type == "application/oebps-package+xml":
            return buf.text.encode()
        elif type == "application/x-dtbncx+xml":
            content = buf.content

            if not content.endswith(b'"UTF-8"?>'):
                return content

            return b'<?xml version="1.0" encoding="UTF-8"?>' + content

        return buf.content

    def _handle_file(self, file: dict) -> bytes:
        if self.args.sleep:
            time.sleep(random.randrange(0, self.args.sleep + 1))

        if self.args.verbose:
            print(file)

        buf = self._fetch_result(file["url"])
        # self.prog_bar.update()

        if file["kind"] == "chapter":
            return self._parse_and_replace_html(buf.content.decode(), file)
        elif file["kind"] == "other_asset":
            return self._handle_xml(file, buf)

        return buf.content

    def zip_epub_contents(self) -> None:
        with ZipFile(
            (
                (OUT_DIR if not self.args.output_dir else self.args.output_dir)
                / "{0}.epub".format(escape_dirname(self.book_info_json["title"]))
            ),
            "w",
            compression=ZIP_DEFLATED,
        ) as handle:

            def _write_to_zip(x):
                handle.writestr(
                    x.file_path,
                    fbytes := (self.files_out / x.file_path).read_bytes(),
                    compresslevel=x.compression_level,
                )
                del fbytes
                gc.collect()

            list(
                map(
                    _write_to_zip,
                    self.file_contents,
                )
            )
            handle.close()

        if not self.args.keep_contents:
            shutil.rmtree(self.files_out)

    def setup_file_contents(self):
        self._collect_stylesheets()

        if list(filter(lambda x: "pdf2htmlEX" in x["filename"], self.file_list)):
            self.is_pdf_converted = True
            print(f"{self.title} is PDF converted. DO NOT USE CALIBRE'S EBOOK-CONVERT!")
            self.file_list = list(
                itertools.filterfalse(
                    lambda x: re.compile("^pdf2htmlEX").match(x["filename"]),
                    self.file_list,
                )
            )

        # TODO: test in future, whether or not to prefer opf with ID instead of content; if present.
        if dup_metadata := list(
            filter(
                lambda x: (
                    ".opf" in x["filename_ext"] and "content" not in x["filename"]
                ),
                self.file_list,
            )
        ):
            list(map(self.file_list.remove, dup_metadata))

        with ProcessPoolExecutor(
            self.args.file_workers_num,
        ) as threads:

            def determine_chunk_size():
                if not self.args.chunksize:
                    return 1

                return (
                    math.ceil(len(self.file_list) / self.args.file_workers_num)
                    if self.args.chunksize and not self.args.chunksize_amount
                    else self.args.chunksize_amount
                )

            self.file_contents = deque(
                threads.map(
                    self._write_file,
                    self.file_list,
                    chunksize=determine_chunk_size(),
                )
            )
            threads.shutdown(wait=True)

        (self.files_out / (relative_mimetype_path := "mimetype")).write_bytes(
            b"application/epub+zip"
        )
        self.file_contents.append(FileData(relative_mimetype_path, 0))

        (
            container_path := (
                self.files_out / (relative_container_path := "META-INF/container.xml")
            )
        ).parent.mkdir(exist_ok=True)
        container_path.write_bytes(
            XML_CONTENTS.format(
                list(filter(lambda x: x["filename_ext"] == ".opf", self.file_list))[0][
                    "filename"
                ]
            ).encode()
        )
        self.file_contents.append(FileData(relative_container_path, 9))

    def _fetch_result(self, url: str) -> requests.Response:
        res = None

        while not res:
            try:
                res = self.cache.get(url)

                if res.status_code == 404 or res.status_code == 403:
                    print(
                        "Oreilly has blacklisted your IP, wait a little or swap IPs before trying again."
                    )
                    sys.exit()
                elif not res.status_code == 200:
                    raise Exception
            except Exception:
                res = None

        return res

    def _write_file(self, x: dict):
        buf = self._handle_file(x)

        file_path = self.files_out / f"OEBPS/{x['full_path']}"
        file_path.parent.mkdir(exist_ok=True, parents=True)
        file_path.write_bytes(buf)

        del buf
        gc.collect()

        return FileData(
            f"OEBPS/{x['full_path']}",
            0 if "image" == x["kind"] else 9,
        )
