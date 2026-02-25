import itertools

from epub import ContentBuffer, OreillyEpubParser

file_contents = {}


def map_files():
    global file_contents
    return list(
        itertools.starmap(
            lambda k, v: ContentBuffer(
                OreillyEpubParser.determine_relative_epub_file_path(k, v[0], v[1]),
                v[2],
                v[3]["level"],
            ),
            file_contents.items(),
        )
    )


def push_filelisting(x):
    global file_contents
    try:
        file_contents[x["file"]["filename"]] = [
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


def start(x, args):
    global file_contents
    parser = OreillyEpubParser(push_filelisting, args)
    parser.get_file_contents()

    mapped_files = map_files()
    parser.zip_epub_contents(mapped_files)
    file_contents.clear()
