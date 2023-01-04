#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from ayaka import Timer
from importlib import import_module
from pathlib import Path
import nonebot
from nonebot.adapters.onebot.v11 import Adapter

nonebot.init()
app = nonebot.get_asgi()
driver = nonebot.get_driver()
driver.register_adapter(Adapter)

with Timer("加载全部插件"):
    for p in Path("plugins").iterdir():
        import_module("plugins." + p.stem)

nonebot.load_from_toml("pyproject.toml")
nonebot.load_plugin("ayaka_test")

if __name__ == "__main__":
    nonebot.run(app="__mp_main__:app")
