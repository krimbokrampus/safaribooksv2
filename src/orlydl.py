import argparse
from collections import deque

from constants import CACHE, OUT_PATH
from epub import OreillyEpubParser
from utils import get_oreilly_cookies

args = argparse.ArgumentParser(
    description="Downloads EPUBs from Oreilly.", add_help=True, allow_abbrev=True
)
args.add_argument(
    "bookid",
    help="Book's ID that you would like to download. You can search the book metadata dump for books.",
)
args.add_argument(
    "--verbose",
    dest="verbose",
    action="store_true",
    help="Prints information about the files as they are requested.",
)
args.add_argument(
    "--sleep",
    dest="sleep",
    action="store_true",
    help="Sleeps when requesting files to prevent IP from being flagged.",
)
args.add_argument(
    "--kindle",
    dest="kindle",
    action="store_true",
    help="Adds CSS rules to block overflow on Kindle Devices.",
)

OUT_PATH.mkdir(exist_ok=True)
CACHE.cookies.update(get_oreilly_cookies())
parser: OreillyEpubParser = OreillyEpubParser(args.parse_args())
book_contents: deque = parser.setup_file_contents()
parser.zip_epub_contents(book_contents)