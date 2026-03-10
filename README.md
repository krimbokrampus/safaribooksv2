# Safaribooks v2 Downloader
> [!WARNING] 
> Oreilly's v2 API seems to hate when you download multiple EPUBs, so they will effectively blacklist the requesting IP temporarily. It'll print and exit the app when this occurs.

> [!NOTE] 
> PRs are welcome! If the recent Safaribooks PRs get merged, I'll defunct this repo. It won't be archived since it still works for PDF-converted EPUBs[^1], whereas [Safaribooks does not](https://github.com/lorenzodifuccia/safaribooks/issues/296).

This is an Oreilly Downloader based on their v2 API. It was rewritten from the minified JS code in the [MyOnlineLearning Downloader](https://my-chrome-extensions.com/) extension – credits to the author for making it! I say this but some things are handled fundamentally different. The extension was more so used for a rudimentary understanding of how things work. I wrote this with 0 knowledge in both HTML and JavaScript (no offense but webdev is boring af). It seems to work for everything, if it doesn't work for you, please make an issue. AI was consulted for specific utilization of methods, NO CODE IS WRITTEN BY IT!

By default, on Windows, it will grab your cookies using your default browser. Firefox may not work, if that is the case: move the Firefox data directory[^2] and login to Oreilly on any [supported Chromium-based browser](https://github.com/borisbabic/browser_cookie3#testing-dates--ddmmyy). For Linux and MacOS, it will instead opt to use one of three browsers: Chrome, Chromium, and Brave. Make sure you are logged-in and have an active Oreilly subscription.

***Obviously – it should go without saying – you should support Oreilly, if you have the means. They graciously provide the books from their catalogue, for which I am certainly thankful. Thanks, Oreilly!***

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

I recommend running calibre's ```ebook-convert``` on the end-result, to rid any inconsistencies. **DO NOT RUN IT ON PDF-CONVERTED EPUBS! IT WILL BREAK THEM!** Terminal will print if your EPUB is PDF-converted, so watch out for that.

**```static/out.json``` is a metadata dump of all Oreilly Books, as of 03/08/26.**

[^1]: Somewhat, see [here](https://github.com/krimbokrampus/safaribooksv2/issues/3)
[^2]: It should contain your profile directory. It's located on ```about:profiles``` in Firefox, under ```Root Directory```. Move/Backup the entire parent directory. If possible, change where it's located, if it's the default directory. Moving it should suffice, though.
