'''便于之后拓展与迁移'''
BOT_TYPE = "nonebot"
# BOT_TYPE = "ayakabot"

# nonebot
if BOT_TYPE == "nonebot":
    from .nonebot_driver import *

# ayaka bot
if BOT_TYPE == "ayakabot":
    from .ayakabot_driver import *
