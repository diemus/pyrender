## Why:
一般来说，遇到复杂的动态页面，大家都会考虑selenium这个工具，但是这个工具有2个缺点，一个是他对并发的支持不好，另一个是selenium是同步的，因此会大幅拖慢爬虫的效率，很难和scrapy这类异步爬虫结合。而chromium有一个基于nodeJS的自动化工具[puppeteer](https://github.com/GoogleChrome/puppeteer)以及相对应的Python版本Pyppeteer，因此可以基于此来构建的异步JavaScript渲染服务。通过http接口的形式进行渲染可以在不修改scrapy调度器源码的情况下让scrapy获得渲染js的能力。

## Usage:
首先安装依赖

    pip install sanic,pyppeteer,aiohttp

然后运行即可：

    python3 pyrender.py

或者后台运行：

    nohup python3 pyrender.py &
   
