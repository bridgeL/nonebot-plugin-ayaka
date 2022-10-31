#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import nonebot
from nonebot.adapters.onebot.v11 import Adapter as ONEBOT_V11Adapter

# 初始化nonebot
nonebot.init()
app = nonebot.get_asgi()
driver = nonebot.get_driver()
driver.register_adapter(ONEBOT_V11Adapter)

# 加载插件
nonebot.load_plugins("plugins")

# 加载测试环境
nonebot.load_plugins("ayaka_test")

# 启动nonebot
if __name__ == "__main__":
    nonebot.run(app="__mp_main__:app")
