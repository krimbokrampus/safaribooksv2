from pathlib import Path

import requests

BASE_URL = "https://learning.oreilly.com"
BOOK_JSON_URL = BASE_URL + "/api/v2/epubs/{0}/"
LIMIT_FORMATTED_URL = "{0}?limit={1}"
FILE_LIST_LIMIT_FORMATTED_URL = (
    BASE_URL + "/api/v2/epubs/urn:orm:book:{0}/files/?limit={2}&offset={1}"
)

XML_CONTENTS = '<?xml version="1.0" encoding="UTF-8"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="{0}" media-type="{1}"/></rootfiles></container>'

KINDLE_CSS = (
    b"#sbo-rt-content *{{word-wrap:break-word!important;"
    b"word-break:break-word!important;}}#sbo-rt-content table,#sbo-rt-content pre"
    b"{{overflow-x:unset!important;overflow:unset!important;"
    b"overflow-y:unset!important;white-space:pre-wrap!important;}}"
)

OUT_DIR = Path("books/")
LOGS_DIR = Path("logs/")

CACHE = requests.Session()
