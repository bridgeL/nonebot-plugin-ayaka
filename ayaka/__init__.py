'''0.5.4b2'''

from loguru import logger
from .ayaka import AyakaApp
from .driver import Message, MessageSegment, Bot, MessageEvent, GroupMessageEvent, Event, DataclassEncoder, msg_type, get_driver, on_message, load_plugin, load_plugins, run
from .config import AyakaConfig, AyakaLargeConfig
from .depend import AyakaDB, AyakaUserDB, AyakaGroupDB, AyakaCache, AyakaInput

# 初始化内置插件
from . import ayaka_master
