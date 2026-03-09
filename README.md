# Safaribooks v2 Downloader
> [!WARNING] 
> Oreilly's v2 API seems to hate when you download multiple EPUBs, so they will effectively blacklist the requesting IP temporarily. It'll print and exit the app when this occurs.

> [!NOTE] 
> PRs are welcome! If the recent Safaribooks PRs get merged, I'll defunct this repo. It won't be archived since it still works for PDF-converted EPUBs (somewhat, see [#3](https://github.com/krimbokrampus/safaribooksv2/issues/3)), whereas [Safaribooks does not](https://github.com/lorenzodifuccia/safaribooks/issues/296). I may or may not make a UI. The ideas I've had work substantially better with a GUI; however, I like the clean, elegant design of a TUI. Bit indecisive, so I decided to hold off, while I work on something else. I may make a draft PR in the future.

This is an Oreilly Downloader based on their v2 API. It was rewritten from the minified JS code in the [MyOnlineLearning Downloader](https://my-chrome-extensions.com/) extension - credits to the author for making it! I say this but some things are handled fundamentally different. The extension was more so used for a rudimentary understanding of how things work. I wrote this with 0 knowledge in both HTML and JavaScript (no offense but webdev is boring af). It seems to work for everything, if it doesn't work for you, please make an issue. AI was consulted for specific utilization of methods, NO CODE IS WRITTEN BY IT!

## Setup
Requires Python 3.14

> [!NOTE] 
> These setup commands are for Linux, specifically. The uv one should work for Windows.

### Using venv:
```bash
git clone https://github.com/krimbokrampus/safaribooksv2
cd safaribooksv2
python -m venv .venv
source .venv/bin/activate # whatever shell you have
pip install -r requirements.txt
python src/main.py <BOOKID>
```

### Using uv:
```bash
git clone https://github.com/krimbokrampus/safaribooksv2
cd safaribooksv2
uv run --with requests --with pyquery --with browser_cookie3 python src/main.py <BOOKID>
```

By default, on Windows, it will grab your cookies using your default browser. Firefox may not work, if that is the case switch to any supported Chromium Browser. For Linux, it will instead opt to use 1 of 3 Browsers: Chrome, Chromium, and Brave. Make sure you are logged-in and have an active Oreilly subscription.

I recommend running calibre's ```ebook-convert``` on the end-result, to rid any inconsistencies. **DO NOT RUN IT ON PDF-CONVERTED EPUBS! IT WILL BREAK THEM!** Terminal will print if your EPUB is PDF converted, so watch out for that.

**```static/out.json``` is a metadata dump of all Oreilly Books, as of 03/08/26.**
