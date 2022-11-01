from playwright.async_api import async_playwright, Browser, Page, Playwright
from contextlib import asynccontextmanager
from typing import AsyncIterator
from nonebot import logger
from .config import fastapi_reload, running_on_windows

_browser: Browser = None
_playwright: Playwright = None


@asynccontextmanager
async def get_new_page(width=None, high_quality=False, **kwargs) -> AsyncIterator[Page]:
    ''' 获取playwright Page对象，width设置屏幕宽度

        使用示例：
        ```
        async with get_new_page(width=200) as p:
            await p.goto(...)
            await p.screenshot(...)
        ```
    '''
    if width:
        kwargs["viewport"] = {"width": width, "height": width}
    if high_quality:
        kwargs["device_scale_factor"] = 2
    page = await _browser.new_page(**kwargs)
    yield page
    await page.close()


async def init_chrome():
    if running_on_windows and fastapi_reload:
        logger.warning("playwright未加载，win平台请关闭fastapi reload功能")
        return

    global _browser, _playwright
    _playwright = await async_playwright().start()
    _browser = await _playwright.chromium.launch()


async def close_chrome():
    if _browser:
        await _browser.close()
    if _playwright:
        await _playwright.stop()
