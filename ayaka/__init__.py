from .ayaka import AyakaApp
from .playwright import get_new_page
from .logger import logger
from .driver import Message, MessageSegment, Bot

# 初始化内置插件
from . import ayaka_master
