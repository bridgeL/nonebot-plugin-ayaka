#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import nonebot
from nonebot.adapters.onebot.v11 import Adapter

# 初始化nonebot
nonebot.init()
app = nonebot.get_asgi()
driver = nonebot.get_driver()
driver.register_adapter(Adapter)


def load():
    # 加载插件
    nonebot.load_plugins("plugins")
    # 加载测试环境
    nonebot.load_plugins("ayaka_test")


reload = getattr(driver.config, "fastapi_reload", True)
if not reload or __name__ == "__mp_main__":
    load()

# 启动nonebot
if __name__ == "__main__":
    nonebot.run(app="__mp_main__:app")
