# 无缝切换ayaka bot
from .ayakabot import Message, MessageSegment, Bot, MessageEvent, GroupMessageEvent, get_driver, on_message, Event, load_plugin, load_plugins, run
from .ayakabot.model import DataclassEncoder

tip = '''
您目前正在使用AYAKA BOT！
注意设置cqhttp连接配置为
- 反向ws
- ws://127.0.0.1:19900/onebot/v11/ws
'''

print(tip)
