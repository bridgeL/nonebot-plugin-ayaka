#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from ayaka.driver import load_plugins, load_plugin, get_driver, run

driver = get_driver()
reload = getattr(driver.config, "fastapi_reload", True)
if not reload or __name__ == "__mp_main__":
    # 加载插件
    load_plugins("plugins")
    # 加载测试环境
    load_plugin("ayaka_test")

# 启动bot
if __name__ == "__main__":
    run()
