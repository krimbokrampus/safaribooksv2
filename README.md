# Safaribooks v2 Downloader
> [!WARNING] 
> Oreilly's v2 API seems to hate when you download multiple EPUBs, so they will effectively blacklist the requesting IP temporarily. It'll print and exit the app when this occurs.

> [!NOTE] 
> PRs are welcome! If the recent Safaribooks PRs get merged, I'll defunct this repo. It won't be archived since it still works for PDF-converted EPUBs[^1], whereas [Safaribooks does not](https://github.com/lorenzodifuccia/safaribooks/issues/296).

> [!NOTE] 
> I recommend running calibre's ```ebook-convert``` on the end-result, to rid any inconsistencies. **DO NOT RUN IT ON PDF-CONVERTED EPUBS! IT WILL BREAK THEM!** Terminal will print if your EPUB is PDF-converted, so watch out for that.

This is an Oreilly Downloader based on their v2 API. It was rewritten from the minified JS code in the [MyOnlineLearning Downloader](https://my-chrome-extensions.com/) extension – credits to the author for making it! I say this but some things are handled fundamentally different. The extension was more so used for a rudimentary understanding of how things work. I wrote this with 0 knowledge in both HTML and JavaScript (no offense but webdev is boring af). It seems to work for everything, if it doesn't work for you, please make an issue. AI was consulted for specific utilization of methods, NO CODE IS WRITTEN BY IT!

By default, it will grab your cookies using your default browser. Firefox-based browser's may not work, if that is the case: move the Firefox-based browser's data directory[^2] and login to Oreilly on any [supported Chromium-based browser](https://github.com/borisbabic/browser_cookie3#testing-dates--ddmmyy). Make sure you are logged-in and have an active Oreilly subscription.

***Obviously – it should go without saying – you should support Oreilly, if you have the means. They graciously provide the books from their catalogue, for which I am certainly thankful. Thanks, Oreilly!***

> [!NOTE]
> **[static/out.json](static/out.json) is a metadata dump of all Oreilly Books, as of 03/08/26.**

## Installing
There are pre-release binaries in releases. Grab the one for your respective OS. Check below for a more direct approach.

### Running
Linux/MacOS
```bash
./main <BOOKID>
```
<br>Windows
```powershell
.\main.exe <BOOKID>
```

## Running Directly
### **Requires Python >=3.14**
Make sure to have [uv](https://docs.astral.sh/uv/getting-started/installation) or [poetry](https://python-poetry.org/docs/#installation).

> [!NOTE] 
> These setup commands have been tested for Linux.

> [!WARNING] 
> If you are using Linux, you will need the following packages: **python3-dev**, **libglib2.0-dev**, and **libdbus-1-dev**. These are Ubuntu-specific, you can figure out the ones you need for your distro [here](https://pkgs.org).

### Using Poetry:
```bash
git clone ...
cd safaribooksv2
poetry install
poetry run src/main.py <BOOKID>
```

#### Updating dependencies:
```bash
poetry update
```

### Using uv:
```bash
git clone ...
cd safaribooksv2
uv python install 3.14
uv sync
uv run src/main.py <BOOKID>
```

## Building Binaries

Make sure pip is in your ```$PATH```.<br>
If it isn't: for Poetry, it should be located in ```$POETRY_VIRTUALENVS_PATH/safaribooksv2-{random-chars}-py3.14/bin``` and for uv, it should be in the project's ```.venv/bin``` directory.

```bash
pip install pyinstaller
pyinstaller src/main.py
```

Or using uv, for convenience:
```bash
uv run pyinstaller main.spec
```

The binary will be available in ```dist/```.

## Contributing
If you know Python – since it's relatively easy to learn – I encourage you to contribute, this repo was made with the goal of having people maintain new Pythonic code, of which the original Safaribooks currently isn't. 

### Why stay with Python?
The answer is simple: to allow more people to help develop the tool. That was the purpose after seeing the stacked amount of PRs in Safaribooks.

## Credits/Licenses
This repo contains the following third-party library (mostly because development died off and it has a bug on Linux).
- [browser_cookie3](https://github.com/borisbabic/browser_cookie3), licensed under [LGPL-3.0](LICENSES/browser_cookie3.LICENSE)

## Project Licensing
This entire work is in the Public Domain, I could care less with what you do to the code.

[^1]: Somewhat, see [here](https://github.com/krimbokrampus/safaribooksv2/issues/3)
[^2]: It should contain your profile directory. It's located on ```about:profiles``` in Firefox, under ```Root Directory```. Move/Backup the entire parent directory. If possible, change where it's located, if it's the default directory. Moving it should suffice, though.
