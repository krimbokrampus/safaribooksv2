import html
import re
import sys
from typing import NamedTuple

from requests import Response

import src.browser_cookie3 as browser_cookie3
from src.constants import CACHE


def format_chapter(book_json, formatted_stylesheets, chapter_content) -> str:
    return '<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE html><html xml:lang="{0}" xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops"><head><title>{1}</title>{2}</head><body><div id="book-content"><div id="sbo-rt-content">{3}</div></body></html>'.format(
        book_json["language"],
        html.escape((book_json["title"])),
        "".join(formatted_stylesheets),
        chapter_content,
    )


def escape_dirname(x) -> str:
    return (
        re.compile(r"[^a-zA-Z0-9_,.\-\"' ]").sub("_", x)
        if "win" in sys.platform
        else x.replace("/", "_")
    )


def fetch(url: str) -> Response:
    res = None

    while not res:
        try:
            res = CACHE.get(url)

            if res.status_code == 404 or res.status_code == 403:
                sys.exit()
            elif not res.status_code == 200:
                raise Exception
        except Exception:
            res = None

    return res


# sourced from https://github.com/azec-pdx/safaribooks/blob/master/retrieve_cookies.py, modified to account for different browsers.
def get_oreilly_cookies(browsers) -> dict:
    domains = [
        # firefox-specific domains:
        "api.oreilly.com",
        ".oreilly.com",
        ".learning.oreilly.com",
        ".www.oreilly.com",
        # chromium-specific domains:
        "learning.oreilly.com",
        "www.oreilly.com",
    ]

    cookies = {}

    def gather_cookies(domain: str):
        cj = browser_cookie3.load(browsers=browsers, domain_name=domain)
        list(map(lambda c: cookies.update({c.name: c.value}), cj))

    list(map(gather_cookies, domains))
    return cookies


class ContentBuffer(NamedTuple):
    file_path: str
    buffer: bytes
    level: int
