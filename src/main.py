import argparse

from epub import OreillyEpubParser

args = argparse.ArgumentParser(
    description="Downloads EPUBs from Oreilly.", add_help=False, allow_abbrev=True
)
args.add_argument(
    "bookid",
    help="Book's ID that you would like to download. You can search the book metadata dump for books.",
)
args.add_argument(
    "--verbose",
    dest="verbose",
    action="store_true",
    help="Prints details about the files, as they are requested. mostly for debugging purposes.",
)
args.add_argument(
    "--sleep",
    dest="sleep",
    action="store_true",
    help="Sleeps when requesting files to prevent IP from being flagged.",
)

parser = OreillyEpubParser(args.parse_args())
book_contents = parser.setup_file_contents()
parser.zip_epub_contents(book_contents)
