# Safaribooks v2 Downloader
> [!WARNING] 
> Oreilly's v2 API seems to hate when you download multiple EPUBs, so they will effectively blacklist the requesting IP temporarily. If you get redundant chapter files in your EPUB, this is the reason.

This is an Oreilly Downloader based on their v2 API. It was rewritten from the minified JS code in the [MyOnlineLearning Downloader](https://my-chrome-extensions.com/) extension - credits to the author for making it! I say this but some things are handled fundamentally differently. The extension was more so used for an understanding of how things work. I wrote this with 0 knowledge in both HTML and JavaScript (no offense but webdev is boring af). It seems to work for everything, if it doesn't work for you, please make an issue. AI was consulted for specific utilization of methods, NO CODE IS WRITTEN BY IT!

## Setup

```bash
git clone https://github.com/krimbokrampus/safaribooksv2
cd safaribooksv2
python -m venv .venv
source .venv/bin/activate # whatever shell you have
pip install -r requirements.txt
python main.py
```

By default, it will grab your cookies using Chrome. If Chrome doesn't exist, it will switch to Firefox. If Firefox doesn't exist, it will fallback to Chromium.

To use it just put the ID you want to download in the main file's func call to ```handler.start()``` or type via input.

**```static/out.json``` is a metadata dump of all Oreilly Books, as of 02/23/26.** <br>
**```static/filelist.json``` is an API dump of ```Machine Learning Foundation```'s filelist for when I was making the Parser.**
