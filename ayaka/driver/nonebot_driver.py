from nonebot.adapters.onebot.v11 import Message, MessageSegment, Bot, MessageEvent, GroupMessageEvent, Event
from nonebot import get_driver, on_message, load_plugins, load_plugin
from nonebot.utils import DataclassEncoder

try:
    import nonebot
    get_driver() # 判断nonebot是否已经初始化
    app = nonebot.get_asgi()
except:
    import nonebot
    from nonebot.adapters.onebot.v11 import Adapter
    nonebot.init()
    driver = nonebot.get_driver()
    driver.register_adapter(Adapter)
    app = nonebot.get_asgi()


def run():
    import nonebot
    nonebot.run(app=f"{__name__}:app")
