from loguru import logger
from nonebot.adapters.onebot.v11 import Message, MessageSegment, Bot, MessageEvent, GroupMessageEvent, Event
from nonebot import get_driver, on_message, load_plugins, load_plugin
from nonebot.utils import DataclassEncoder
from ..config import ayaka_root_config

try:
    import nonebot
    get_driver()  # 判断nonebot是否已经初始化
    app = nonebot.get_asgi()
except:
    import nonebot
    nonebot.init()
    logger.warning("由于ayaka在nonebot初始化前被调用，ayaka内部已自动完成nonebot的初始化工作")

    # 默认使用OnebotV11适配器
    from nonebot.adapters.onebot.v11 import Adapter
    driver = nonebot.get_driver()
    driver.register_adapter(Adapter)
    app = nonebot.get_asgi()

    # 传递端口号
    ayaka_root_config.ayaka_port = driver.config.port


def run():
    import nonebot
    nonebot.run(app=f"{__name__}:app")
