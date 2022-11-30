#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 读取bot类型
import json
from pathlib import Path
bot_type = "nonebot"

path = Path("ayaka_setting.json")
if path.exists():
    with path.open("r", encoding="utf8") as f:
        data = json.load(f)
        bot_type = data["__root__"]["bot_type"]

# 根据bot类型加载对应方法
if bot_type == "ayakabot":
    from ayaka.driver.ayakabot import run, load_plugins, load_plugin, get_driver
    driver = get_driver()

if bot_type == "nonebot":
    import nonebot
    from nonebot import load_plugin, load_plugins, run
    from nonebot.adapters.onebot.v11 import Adapter

    # 初始化nonebot
    nonebot.init()
    driver = nonebot.get_driver()
    driver.register_adapter(Adapter)
    app = nonebot.get_asgi()

    def run():
        nonebot.run(app=f"__mp_main__:app")

# 加载插件
reload = getattr(driver.config, "fastapi_reload", True)
if not reload or __name__ == "__mp_main__":
    load_plugins("plugins")
    # 加载测试环境
    load_plugin("ayaka_test")

# 启动bot
if __name__ == "__main__":
    run()
