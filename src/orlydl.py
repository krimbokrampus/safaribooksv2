import argparse
import gc
import json
import sys
from concurrent.futures import ThreadPoolExecutor, wait
from pathlib import Path

import browser_cookie3
from constants import CACHE, OUT_DIR
from epub import OreillyEpubParser
from utils import get_oreilly_cookies

if __name__ == "__main__":
    args = argparse.ArgumentParser(
        description="Downloads EPUBs from Oreilly.", add_help=True, allow_abbrev=True
    )
    args.add_argument(
        "-i",
        "--iden",
        dest="iden",
        action="extend",
        nargs="+",
        type=str,
        help="Book's ID that you would like to download, can be multiple. You can search the book metadata dump for books.",
    )
    args.add_argument(
        "-m",
        "--batch",
        dest="file_list",
        nargs="?",
        type=Path,
        help="File list of identifiers, separated by newlines.",
    )
    args.add_argument(
        "-c",
        "--cookies",
        dest="cookie_file",
        nargs="?",
        type=Path,
        help="Path to JSON containing your cookies.",
    )
    args.add_argument(
        "-o",
        "--output",
        dest="output_dir",
        nargs="?",
        type=Path,
        help="Books output directory.",
    )
    args.add_argument(
        "-t",
        "--threads-num",
        dest="threads_num",
        type=int,
        default=2,
        help="Maximum concurrent books to download. Recommended: 4, Max: 8-6.",
    )
    args.add_argument(
        "-f",
        "--file-threads-num",
        dest="file_threads_num",
        type=int,
        default=3,
        help="Maximum concurrent number of files to download. Recommended: 3, Max: 8-6.",
    )
    args.add_argument(
        "-b",
        "--browser",
        choices=browser_cookie3.BROWSERS,  # validates input + powers tab-completion
        action="append",
        dest="browsers",
        metavar="BROWSER",
        help="Browser(s) to load cookies from (default: all).",
    )
    args.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="store_true",
        help="Prints information about the files as they are requested.",
    )
    args.add_argument(
        "-s",
        "--sleep",
        dest="sleep",
        action="store_true",
        help="Sleeps when requesting files to prevent IP from being flagged.",
    )
    args.add_argument(
        "-k",
        "--kindle",
        dest="kindle",
        action="store_true",
        help="Adds CSS rules to block overflow on Kindle Devices.",
    )

    args = args.parse_args()
    OUT_DIR.mkdir(exist_ok=True) if not args.output_dir else args.output_dir.mkdir(
        exist_ok=True
    )
    CACHE.cookies.update(
        get_oreilly_cookies(args.browsers)
        if not args.cookie_file
        else json.load(args.cookie_file.open())
    )

    def parse_iden(x: str, args: argparse.Namespace):
        parser = OreillyEpubParser(x, args)
        book_contents = parser.setup_file_contents()
        parser.zip_epub_contents(book_contents)

        del parser, book_contents
        gc.collect()

    if isinstance(args.iden, list) and len(args.iden) > 1:
        total = len(args.iden)

        with ThreadPoolExecutor(args.threads_num) as threads:
            futures = []

            [
                futures.append(threads.submit(parse_iden, iden, args))
                for iden in args.iden
            ]
            done = wait(futures, return_when="FIRST_EXCEPTION")

            threads.shutdown()

        sys.exit()
    elif args.file_list:
        items = list(map(lambda x: x.removeprefix("\n"), args.file_list.read_text()))
        total = len(items)

        print("Total books: " + str(total))

        with ThreadPoolExecutor(args.threads_num) as threads:
            futures = []

            [futures.append(threads.submit(parse_iden, iden, args)) for iden in items]
            done = wait(futures, return_when="FIRST_EXCEPTION")

            threads.shutdown()

        sys.exit()
    else:
        parse_iden(args.iden[0], args)
        sys.exit()
