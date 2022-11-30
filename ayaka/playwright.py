from .driver import get_driver
import platform
from loguru import logger
from .config import ayaka_root_config

running_on_windows = platform.system() == "Windows"
fastapi_reload = getattr(get_driver().config, "fastapi_reload", True)

if ayaka_root_config.use_playwright:
    import datetime
    from playwright.async_api import async_playwright, Browser, Page, Playwright
    from contextlib import asynccontextmanager
    from typing import AsyncIterator
    from .driver import get_driver

    driver = get_driver()
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
        with open("test.log", "a+", encoding="utf8") as f:
            d = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{d}] 记录时间  playwright init\n")
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
        with open("test.log", "a+", encoding="utf8") as f:
            d = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{d}] 记录时间  playwright close\n")
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
