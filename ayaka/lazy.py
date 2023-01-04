'''懒人包'''
from loguru import logger
from pathlib import Path
from pydantic import Field, BaseModel
from nonebot.rule import Rule
from nonebot.typing import T_State
from nonebot import on_command, on_message, get_driver
from nonebot.adapters.onebot.v11.helpers import Numbers
from nonebot.adapters.onebot.v11 import GroupMessageEvent, PrivateMessageEvent, Message, MessageSegment, Bot
