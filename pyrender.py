from sanic import Sanic
from sanic.response import json, html
from pyppeteer import launch, errors
from pyppeteer.errors import PageError, TimeoutError, NetworkError
import json
import aiohttp
import asyncio
import traceback

app = Sanic()


async def fetch(request):
    proxy = request.headers.get('self-proxy')
    if proxy:
        del request.headers['self-proxy']
    async with aiohttp.ClientSession() as session:
        try:
            async with session.request(request.method, request.url, headers=request.headers, data=request.postData,
                                       proxy=proxy, verify_ssl=False) as res:
                data = {
                    'headers': dict(res.headers),
                    'status': res.status,
                    'body': await res.read(),
                }
                return data
        except Exception:
            return {
                'headers': {},
                'status': 500,
                'body': b'',
            }


async def filter_request(request):
    blacklist = ['stylesheet', 'image', 'media', 'font', 'texttrack']
    fetch_list = ['document']
    # print(request.resourceType)
    if request.resourceType in blacklist:
        await request.abort()
    else:
        res = await fetch(request)
        await request.respond(res)


main_browser = None


async def get_browser():
    browser_args = [
        '--ignore-certificate-errors',
    ]
    global main_browser
    if not main_browser:
        main_browser = await launch(headless=True, ignoreHTTPSErrors=True, args=browser_args)
    return main_browser


def get_navigation_promise(page, wait_func, wait_args):
    func_map = [
        'waitFor',
        'waitForNavigation',
        'waitForSelector',
        'waitForXPath',
        'waitForFunction',
        'waitForResponse',
        'waitForRequest',
    ]
    func = getattr(page, wait_func)
    return asyncio.ensure_future(func(**wait_args))


@app.route('/render')
async def render(request):
    url = request.args.get('url')
    timeout = int(request.args.get('timeout', 30)) * 1000
    proxy = request.args.get('proxy')
    headers = json.loads(request.args.get('headers', '{}'))
    wait_func = request.args.get('wait_func', 'waitForNavigation')
    wait_args = json.loads(request.args.get('wait_args', '{}'))
    if proxy:
        headers['self-proxy'] = proxy

    browser = await get_browser()
    page = await browser.newPage()
    # 设置默认超时时间
    page.setDefaultNavigationTimeout(timeout)
    # 修改请求头
    await page.setExtraHTTPHeaders(headers)
    # 过滤无用请求
    await page.setRequestInterception(True)
    page.on('request', filter_request)

    status = None
    content = ''
    try:
        navigation_promise = get_navigation_promise(page, wait_func, wait_args)
        response = await page.goto(url)
        # 重复的url不会再重复请求，response为None
        status = response.status if response else 200
        print(response)
        await navigation_promise
        content = await page.content()
    except TimeoutError:
        # 等待超时，网页可能已经加载完成，只是判断指标有有误，读取过晚
        content = await page.content()
    except Exception:
        # 其他错误直接跳过
        traceback.print_exc()
    finally:
        await page.close()
        return html(content, status=status if status else 500)

if __name__ == '__main__':
    # 初始化浏览器
    app.add_task(get_browser())
    app.run(host='0.0.0.0', port=9000)

