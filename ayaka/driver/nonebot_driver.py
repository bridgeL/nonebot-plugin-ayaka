from nonebot.adapters.onebot.v11 import Message, MessageSegment, Bot, MessageEvent, GroupMessageEvent, Event
from nonebot import get_driver, on_message, load_plugins, load_plugin
from nonebot.utils import DataclassEncoder


def init():
    import nonebot
    from nonebot.adapters.onebot.v11 import Adapter

    # 初始化nonebot
    nonebot.init()
    driver = nonebot.get_driver()
    driver.register_adapter(Adapter)


def run():
    import nonebot
    app = nonebot.get_asgi()
    nonebot.run(app="__mp_main__:app")
