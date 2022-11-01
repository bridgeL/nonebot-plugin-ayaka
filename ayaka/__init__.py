'''安全起见，避免变量冲突'''
from .ayaka import AyakaApp
from .playwright import get_new_page
from .storage import AyakaLocalPath, AyakaPath
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot import logger

# 初始化内置插件
from . import ayaka_master
