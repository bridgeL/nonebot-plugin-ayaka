from loguru import logger
from .ayaka import AyakaApp
from .playwright import get_new_page
from .driver import Message, MessageSegment, Bot, get_driver

# 初始化内置插件
from . import ayaka_master
