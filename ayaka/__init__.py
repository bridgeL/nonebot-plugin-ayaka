#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from loguru import logger
from .ayaka import AyakaApp
from .playwright import get_new_page
from .driver import Message, MessageSegment, Bot, get_driver
from .state import AyakaStateBase
from .ayaka_input import AyakaInputModel, msg_type

# 初始化内置插件
from . import ayaka_master
