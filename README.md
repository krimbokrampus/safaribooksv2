# Safaribooks v2 Downloader
> [!WARNING] 
> Oreilly's v2 API seems to hate when you download multiple EPUBs, so they will effectively blacklist the requesting IP temporarily. It'll print and exit the app when this occurs.

> [!NOTE] 
> PRs are welcome! I do ask that you conform to my style; though, it's not explicitly required. I use Ruff and ty. I've got a rough idea of where to take the TUI, so I'll be working on that.

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

By default, it will grab your cookies using Chrome. If Chrome doesn't exist, it will switch to Firefox. If Firefox doesn't exist, it will fallback to Chromium.

I recommend running calibre's ```ebook-convert``` on the end-result, to rid any inconsistencies. **DO NOT RUN IT ON PDF-CONVERTED EPUBS! IT WILL BREAK THEM!** Terminal will print if your EPUB is PDF converted, so watch out for that.

**```static/out.json``` is a metadata dump of all Oreilly Books, as of 02/26/26.** <br>
**```static/filelist.json``` is an API dump of ```Handbook of International Economics```'s filelist for when I was making the Parser.**
