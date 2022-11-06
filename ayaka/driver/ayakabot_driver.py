# 无缝切换ayaka bot
from .ayakabot import Message, MessageSegment, Bot, MessageEvent, GroupMessageEvent, get_driver, on_message

tip = '''
您目前正在使用AYAKA BOT！
注意设置cqhttp连接配置为
- 反向ws
- ws://127.0.0.1:19900/ayakabot
'''

print(tip)
