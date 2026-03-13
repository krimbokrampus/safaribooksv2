import argparse
import gc
import sys
from concurrent.futures import ProcessPoolExecutor, wait
from multiprocessing import freeze_support
from pathlib import Path

import browser_cookie3
import epub
from constants import OUT_DIR

if __name__ == "__main__":
    if sys.platform == "win32":
        freeze_support()

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
        "-w",
        "--file-workers-num",
        dest="file_workers_num",
        type=int,
        default=3,
        help="Maximum concurrent number of files to download. Recommended: 3, Max: 8-6.",
    )
    args.add_argument(
        "--file-workers-chunksize",
        dest="chunksize",
        nargs="?",
        help="Whether or not to enable file batching while multithreading the file downloads.",
    )
    args.add_argument(
        "--file-workers-chunksize-num",
        dest="chunksize_amount",
        type=int,
        nargs="?",
        help="Amount of files to split per file worker. By default, it will be the smallest number closest to the total number of files / --file-workers-num/-w",
    )
    args.add_argument(
        "-b",
        "--browser",
        choices=browser_cookie3.BROWSERS,
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
        nargs="?",
        type=int,
        help="Sleeps when requesting files to prevent IP from flagged. This will be a random digit between 0 and this number for each file before being requested. Results may vary.",
    )
    args.add_argument(
        "-k",
        "--kindle",
        dest="kindle",
        action="store_true",
        help="Adds CSS rules to block overflow on Kindle Devices.",
    )
    args.add_argument(
        "--keep-tmp-files",
        dest="keep_contents",
        action="store_true",
        help="Keeps the temp files of each book's contents rather than removing them outright.",
    )

    args = args.parse_args()
    epub.ARGS = args
    OUT_DIR.mkdir(
        exist_ok=True
    ) if not epub.ARGS.output_dir else epub.ARGS.output_dir.mkdir(exist_ok=True)

    def parse_iden(x: str):
        parser = epub.OreillyEpubParser(x)
        parser.setup_file_contents()
        parser.zip_epub_contents()

        del parser
        gc.collect()

    if len(args.iden) == 1:
        parse_iden(epub.ARGS.iden[0])
        sys.exit()
    elif epub.ARGS.file_list or len(args.iden) > 1:
        with ProcessPoolExecutor(epub.ARGS.threads_num) as pool:
            futures = list(
                map(
                    lambda x: pool.submit(parse_iden, x),
                    total_books := list(
                        map(
                            lambda x: x.removeprefix("\n"),
                            epub.ARGS.file_list.read_text(),
                        )
                    )
                    if epub.ARGS.file_list
                    else epub.ARGS.iden,
                )
            )
            print("Total books: " + str(len(total_books)))
            done, not_done = wait(futures, return_when="FIRST_EXCEPTION")

            if not_done:
                print("An error occurred and a book failed to download.")

            pool.shutdown()

        sys.exit()
