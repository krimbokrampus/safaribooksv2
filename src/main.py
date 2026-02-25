import argparse

import handler

args = argparse.ArgumentParser(
    description="Downloads EPUBs from Oreilly.", add_help=False, allow_abbrev=False
)
args.add_argument(
    "bookid",
    help="Book's ID that you would like to download. You can search the book metadata dump for books.",
)
args.add_argument(
    "--verbose",
    dest="verbose",
    action="store_true",
    help="Prints the files as they are scraped.",
)
args.add_argument(
    "--sleep",
    dest="sleep",
    action="store_true",
    help="Sleeps when requesting files to prevent IP from being flagged.",
)

handler.start(args.parse_args())
