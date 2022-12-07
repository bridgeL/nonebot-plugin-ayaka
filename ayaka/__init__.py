#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from loguru import logger
from .ayaka import AyakaApp
from .playwright import get_new_page
from .driver import *
from .input import AyakaInput
from .cache import AyakaCache
from .config import AyakaPluginConfig

# 初始化内置插件
from . import ayaka_master
