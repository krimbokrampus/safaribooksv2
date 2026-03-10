import html
import re
import sys
from typing import NamedTuple, Optional

import browser_cookie3
from requests import Response

from constants import CACHE


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


def fetch(url: str) -> Optional[Response]:
    res = None

    while not res:
        try:
            res = CACHE.get(url)

            if res.status_code == 404:
                return None
            elif not res.status_code == 200:
                raise Exception
        except Exception:
            res = None

    return res


# sourced from https://github.com/azec-pdx/safaribooks/blob/master/retrieve_cookies.py, modified to account for different browsers.
def get_oreilly_cookies() -> dict:
    domains = [
        "learning.oreilly.com",
        "www.oreilly.com",
        ".oreilly.com",
        "oreilly.com",
        "api.oreilly.com",
    ]

    cookies = {}
    browser = None

    if "linux" == sys.platform:
        try:
            try:
                _ = browser_cookie3.chrome()
                browser = "chrome"
            except browser_cookie3.BrowserCookieError:
                print("failed to locate chrome cookies")
                _ = browser_cookie3.brave()
                browser = "brave"
        except browser_cookie3.BrowserCookieError:
            print("failed to locate brave cookies")
            browser = "chromium"

    def scrape_cookie(domain: str):
        if "win" in sys.platform:
            cj = browser_cookie3.load(domain_name=domain)  # func broke on linux
        else:
            match browser:
                case "chrome":
                    cj = browser_cookie3.chrome(domain_name=domain)
                case "brave":
                    cj = browser_cookie3.brave(domain_name=domain)
                case "chromium":
                    cj = browser_cookie3.chromium(domain_name=domain)
        list(map(lambda c: cookies.update({c.name: c.value}), cj))

    list(map(scrape_cookie, domains))
    return cookies


class ContentBuffer(NamedTuple):
    file_path: str
    buffer: bytes
    level: int
