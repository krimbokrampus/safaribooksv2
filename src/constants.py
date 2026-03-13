from pathlib import Path

import enlighten
from enlighten.manager import Manager

BASE_URL: str = "https://learning.oreilly.com"
BOOK_JSON_URL: str = BASE_URL + "/api/v2/epubs/{0}/"
LIMIT_FORMATTED_URL: str = "{0}?limit={1}"
FILE_LIST_LIMIT_FORMATTED_URL: str = (
    BASE_URL + "/api/v2/epubs/urn:orm:book:{0}/files/?limit={2}&offset={1}"
)

XML_CONTENTS: str = '<?xml version="1.0" encoding="UTF-8"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/{0}" media-type="application/oebps-package+xml"/></rootfiles></container>'

KINDLE_CSS: bytes = (
    b"#sbo-rt-content *{{word-wrap:break-word!important;"
    b"word-break:break-word!important;}}#sbo-rt-content table,#sbo-rt-content pre"
    b"{{overflow-x:unset!important;overflow:unset!important;"
    b"overflow-y:unset!important;white-space:pre-wrap!important;}}"
)

OUT_DIR: Path = Path("books/")
PBCTX_MANAGER: Manager = enlighten.get_manager()
