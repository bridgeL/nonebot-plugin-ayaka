'''浏览器截图'''
import platform
from loguru import logger
from .config import ayaka_root_config
from .driver import get_driver

driver = get_driver()
running_on_windows = platform.system() == "Windows"
fastapi_reload = getattr(driver.config, "fastapi_reload", True)

if ayaka_root_config.use_playwright:
    from playwright.async_api import async_playwright, Browser, Page, Playwright
    from contextlib import asynccontextmanager
    from typing import AsyncIterator

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

    @driver.on_startup
    async def startup():
        print('''

    playwright init

        ''')
        if running_on_windows and fastapi_reload:
            logger.warning("playwright未加载，win平台请关闭fastapi reload功能")
            return

        global _browser, _playwright
        _playwright = await async_playwright().start()
        _browser = await _playwright.chromium.launch()

    @driver.on_shutdown
    async def shutdown():
        # 查bug 怀疑卡死原因是没有正确退出
        print('''

    playwright close

        ''')
        if _browser:
            await _browser.close()
        if _playwright:
            await _playwright.stop()
else:
    async def get_new_page(width=None, high_quality=False, **kwargs):
        logger.warning("ayaka未开启playwright功能")
