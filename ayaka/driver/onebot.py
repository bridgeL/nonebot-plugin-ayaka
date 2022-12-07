from ..config import ayaka_root_config

# nonebot
if ayaka_root_config.bot_type == "nonebot":
    from .nonebot_driver import *

# ayaka bot
if ayaka_root_config.bot_type == "ayakabot":
    from .ayakabot_driver import *
