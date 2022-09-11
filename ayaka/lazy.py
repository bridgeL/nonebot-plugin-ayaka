'''快捷导入'''
from .model import AyakaBot, AyakaDevice, AyakaApp, Storage, Cache, Trigger, create_path, create_file, beauty_save
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageEvent, Message, MessageSegment
from nonebot import logger