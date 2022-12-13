#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from ayaka import load_plugins, load_plugin, run
from ayaka.extension import Timer

with Timer("加载全部插件"):
    load_plugins("plugins")

# 加载测试环境
load_plugin("ayaka_test")

# 启动bot
if __name__ == "__main__":
    run()
