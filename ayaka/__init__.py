'''安全起见，避免变量冲突'''
from .ayaka import AyakaApp, AyakaStorage, get_new_page
from nonebot.adapters.onebot.v11.exception import ActionFailed, NetworkError, OneBotV11AdapterException
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot import logger

# 初始化内置插件
from . import ayaka_master
