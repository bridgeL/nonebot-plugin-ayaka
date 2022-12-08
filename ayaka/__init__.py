#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from loguru import logger
from .ayaka import AyakaApp
from .playwright import get_new_page
from .driver import *
from .config import AyakaConfig, AyakaLargeConfig
from .depend import AyakaDB, AyakaUserDB, AyakaGroupDB, AyakaCache, AyakaInput

# 初始化内置插件
from . import ayaka_master
