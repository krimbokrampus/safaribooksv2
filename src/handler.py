import asyncio
import itertools

from epub import ContentBuffer, OreillyEpubParser

i = {}


def map_files():
    global i
    return list(
        itertools.starmap(
            lambda k, v: ContentBuffer(
                OreillyEpubParser.determine_relative_epub_file_path(k, v[0], v[1]),
                v[2],
                v[3]["level"],
            ),
            i.items(),
        )
    )


def push_filelisting(x):
    global i
    try:
        i[x["file"]["filename"]] = [
            x["file"]["filename_ext"],
            x["file"]["full_path"],
            x["fileContents"],
            {
                "level": 0
                if "image" == x["file"]["kind"] or "mimetype" == x["file"]["full_path"]
                else 9
            },
        ]
    except KeyError:
        print(x["file"])


def start(x):
    global i
    parser = OreillyEpubParser(x, push_filelisting)
    asyncio.run(parser.get_file_contents())

    mapped_files = map_files()
    parser.zip_epub_contents(mapped_files)
    i.clear()
