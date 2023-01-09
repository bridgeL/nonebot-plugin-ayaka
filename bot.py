#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ---- nonebot ----
import nonebot
nonebot.init()
app = nonebot.get_asgi()
driver = nonebot.get_driver()

# 注册适配器
from nonebot.adapters.onebot.v11 import Adapter
driver.register_adapter(Adapter)

# # ---- 搞事 ----
# import ayaka.patch as hack
# # 统计加载时间
# hack.hack_load_plugin()

# ---- 加载插件 ----
# nonebot.load_plugin("test")
# nonebot.load_plugin("ayaka_games")
# nonebot.load_from_toml("pyproject.toml")
nonebot.load_plugin("ayaka_test")


if __name__ == "__main__":
    nonebot.run(app="__mp_main__:app")
