# Safaribooks v2 Downloader
This is an Oreilly Downloader based on their v2 API. It was rewritten from the minified JS code in the [MyOnlineLearning Downloader](https://my-chrome-extensions.com/) extension - credits to them for making it! I wrote it with 0 knowledge in both HTML and JavaScript. It seems to work for everything but PDF's adapted to xHTML format. I'm trying to fix that problem, though. AI was consulted for specific utilization of methods, NO CODE IS WRITTEN BY IT!

By default, it will grab your cookies using Chromium. If you don't have Chromium, then you can change ```cj = browser_cookie3.chromium(domain_name=d)``` to your specific browser. It's in ```src/epub.py``` at L77.

To use it just put the ID you want to download in the main file's func call to ```handler.start()``` or type via input.

## **```static/out.json``` is a metadata dump of all Oreilly Books, as of 02/20/26.**
## **```static/filelist.json``` is an API dump of ```Machine Learning Foundation```'s filelist for when I was making the Parser.**
