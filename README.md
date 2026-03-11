# Safaribooks v2 Downloader
> [!WARNING] 
> Oreilly's v2 API seems to hate when you download multiple EPUBs, so they will effectively blacklist the requesting IP temporarily. It'll print and exit the app when this occurs.

> [!NOTE] 
> PRs are welcome! If the recent Safaribooks PRs get merged, I'll defunct this repo. It won't be archived since it still works for PDF-converted EPUBs[^1], whereas [Safaribooks does not](https://github.com/lorenzodifuccia/safaribooks/issues/296).

> [!IMPORTANT] 
> I recommend running calibre's ```ebook-convert``` on the end-result, to rid any inconsistencies. **DO NOT RUN IT ON PDF-CONVERTED EPUBS! IT WILL BREAK THEM!** Terminal will print if your EPUB is PDF-converted, so watch out for that.

This is an Oreilly Downloader based on their v2 API. It was rewritten from the minified JS code in the [MyOnlineLearning Downloader](https://my-chrome-extensions.com/) extension – credits to the author for making it! I say this but some things are handled fundamentally different. The extension was more so used for a rudimentary understanding of how things work. I wrote this with 0 knowledge in both HTML and JavaScript (no offense but webdev is boring af). It seems to work for everything, if it doesn't work for you, please make an issue. AI was consulted for specific utilization of methods, NO CODE IS WRITTEN BY IT!

By default, it will grab your cookies using your default browser. Make sure you are logged-in and have an active Oreilly subscription. Firefox-based browsers may not work, if that is the case: login to Oreilly on any [supported Chromium-based browser](https://github.com/borisbabic/browser_cookie3#testing-dates--ddmmyy) and specify the browsers name via ```-b/--browser```. If that doesn't work, as a last resort, use the following script in your dev console (on Oreilly's homepage) to export a ```cookies.json``` and pass it via ```-c/--cookies```.

```JavaScript
const cookies = document.cookie.split(';').reduce((acc, cookie) => {
  const [key, val] = cookie.trim().split('=');
  if (['_abck', 'bm_sz', 'orm-jwt', 'orm-rt'].includes(key)) {
    acc[key] = val;
  }
  return acc;
}, {});

const blob = new Blob([JSON.stringify(cookies, null, 2)], {type: 'application/json'});
const url = URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = 'cookies.json';
a.click();
```

> [!IMPORTANT]
> ***Obviously – it should go without saying – you should support Oreilly, if you have the means. They graciously provide the books from their catalogue, for which I am certainly thankful. Thanks, Oreilly!***

> [!IMPORTANT]
> **[static/out.json](static/out.json) is a metadata dump of all Oreilly Books, as of 03/11/26.**

## Installation
There are binaries [here](https://github.com/krimbokrampus/safaribooksv2/releases/latest). Grab the one for your respective OS. Read below for a more direct approach.

### Running
Linux/MacOS
```bash
./orlydl <BOOKID>
```
<br>Windows
```powershell
.\orlydl.exe <BOOKID>
```

### Argument Help
```
usage: orlydl [-h] [-i IDEN [IDEN ...]] [-m [FILE_LIST]] [-c [COOKIE_FILE]]
              [-o [OUTPUT_DIR]] [-t THREADS_NUM] [-f FILE_THREADS_NUM] [-b BROWSER]
              [-v] [-s] [-k]

Downloads EPUBs from Oreilly.

options:
  -h, --help            show this help message and exit
  -i, --iden IDEN [IDEN ...]
                        Book's ID that you would like to download, can be multiple.
                        You can search the book metadata dump for books.
  -m, --batch [FILE_LIST]
                        File list of identifiers, separated by newlines.
  -c, --cookies [COOKIE_FILE]
                        Path to JSON containing your cookies.
  -o, --output [OUTPUT_DIR]
                        Books output directory.
  -t, --threads-num THREADS_NUM
                        Maximum concurrent books to download. Recommended: 4, Max:
                        8-6.
  -f, --file-threads-num FILE_THREADS_NUM
                        Maximum concurrent number of files to download. Recommended:
                        3, Max: 8-6.
  -b, --browser BROWSER
                        Browser(s) to load cookies from (default: all).
  -v, --verbose         Prints information about the files as they are requested.
  -s, --sleep           Sleeps when requesting files to prevent IP from being flagged.
  -k, --kindle          Adds CSS rules to block overflow on Kindle Devices.
```

## Running Directly
### **Requires Python >=3.14**
Make sure to have [uv](https://docs.astral.sh/uv/getting-started/installation) or [Poetry](https://python-poetry.org/docs/#installation).

> [!NOTE] 
> These setup commands have been tested for Linux.

> [!IMPORTANT] 
> If you are using Linux, you will need the following packages: **python3-dev**, **libglib2.0-dev**, and **libdbus-1-dev**. These are Ubuntu-specific, you can figure out the ones you need for your distro [here](https://pkgs.org).

### Start:
```
git clone ...
cd safaribooksv2
```

### Using Python Directly:
```bash
pip install -r requirements.txt
python src/orlydl.py <BOOKID>
```

### Using uv (recommended):
```bash
uv python install 3.14
uv sync
uv run src/orlydl.py <BOOKID>
```

### Using Poetry:
```bash
poetry install
poetry run src/orlydl.py <BOOKID>
```

### Using venv:
```bash
python -m venv .venv
source .venv/bin/activate # whatever shell you have, or call the cmds directly
pip install -r requirements.txt
python src/orlydl.py <BOOKID>
```

### Updating Dependencies:

#### **uv**
```bash
uv lock --upgrade
```

Manually updating specific packages for uv:
```
uv pip list --outdated
uv lock --upgrade-package <package>
```
uv does not have automatic dependency management for ```pyproject.toml```, [yet](https://github.com/astral-sh/uv/pull/13934).

#### **Poetry**
```bash
poetry update
```

### If Dependencies Are Updated and You Plan on Contributing

#### **uv**
```bash
uv export --format requirements.txt -o requirements.txt --no-hashes
```

#### **Poetry**
```bash
# If you are on Linux and it fails, install it from your package manager.
poetry self add poetry-plugin-export
poetry export --output requirements.txt --without-hashes
```

This ensures the requirements are updated for those who don't use Poetry or uv.

## Building Binaries
Make sure pip is in your ```$PATH```[^3].

```bash
pip install pyinstaller
pyinstaller src/orlydl.py
```

Or using uv, for convenience:
```bash
uv run pyinstaller src/orlydl.spec
```

The binary will be available in ```$PWD/dist/orlydl```.

## Contributing
If you know Python – since it's relatively easy to learn – I encourage you to contribute. This repo was made with the goal of having people maintain new Pythonic code, of which the original Safaribooks currently isn't. 

### Why stay with Python?
The answer is simple: to allow more people to help develop the tool. That was the purpose after seeing the stacked amount of PRs in Safaribooks.

## Credits/Licenses
This repo contains the following third-party library (mostly because development died off and it has a bug on Linux).
- [browser_cookie3](https://github.com/borisbabic/browser_cookie3), licensed under [LGPL-3.0](LICENSES/browser_cookie3.LICENSE)

## Project Licensing
This entire work is in the Public Domain, I could care less with what you do to the code.

[^1]: Somewhat, see [here](https://github.com/krimbokrampus/safaribooksv2/issues/3)
[^2]: If it isn't: for Poetry, it should be located in ```$POETRY_VIRTUALENVS_PATH/safaribooksv2-{random-chars}-py3.14/bin``` and for uv, it should be in the project's ```.venv/bin``` directory.
