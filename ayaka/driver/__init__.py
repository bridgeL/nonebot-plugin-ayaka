'''便于之后拓展与迁移'''
BOT_TYPE = "nonebot"
# BOT_TYPE = "ayakabot"

# nonebot
if BOT_TYPE == "nonebot":
    try:
        from .nonebot_driver import *
    except:
        # 如果没有安装nonebot则无缝切换ayaka bot
        BOT_TYPE = "ayakabot"
        from .ayakabot_driver import *

# ayaka bot
else:
    from .ayakabot_driver import *
