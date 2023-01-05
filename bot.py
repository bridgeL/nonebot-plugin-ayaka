#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import nonebot
from nonebot.adapters.onebot.v11 import Adapter
from ayaka import load_cwd_plugins, Timer

nonebot.init()
app = nonebot.get_asgi()
driver = nonebot.get_driver()
driver.register_adapter(Adapter)

with Timer("加载全部插件"):
    load_cwd_plugins("plugins")
nonebot.load_from_toml("pyproject.toml")
nonebot.load_plugin("ayaka_test")

if __name__ == "__main__":
    nonebot.run(app="__mp_main__:app")
