#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import nonebot
from nonebot.adapters.onebot.v11 import Adapter

nonebot.init()
app = nonebot.get_asgi()
driver = nonebot.get_driver()
driver.register_adapter(Adapter)

from ayaka import Timer
with Timer("加载全部插件"):
    nonebot.load_plugins("plugins")

import ayaka_games
nonebot.load_from_toml("pyproject.toml")
nonebot.load_plugin("ayaka_test")

if __name__ == "__main__":
    nonebot.run(app="__mp_main__:app")
