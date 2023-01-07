#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import nonebot
from nonebot.adapters.onebot.v11 import Adapter

nonebot.init()
app = nonebot.get_asgi()
driver = nonebot.get_driver()
driver.register_adapter(Adapter)

from ayaka.patch import money_patch_PluginManager_load_plugin
money_patch_PluginManager_load_plugin()
nonebot.load_plugin("ayaka_games")
nonebot.load_from_toml("pyproject.toml")
# nonebot.load_plugin("ayaka_test")

if __name__ == "__main__":
    nonebot.run(app="__mp_main__:app")
