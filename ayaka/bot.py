from typing import Dict
from nonebot import get_driver
from nonebot.adapters.onebot.v11 import Bot
from .model import AyakaBot
driver = get_driver()

# ayaka_bot
ayaka_bots: Dict[str, AyakaBot] = {}


@driver.on_bot_connect
async def add_bot(bot: Bot):
    if bot.self_id not in ayaka_bots:
        ayaka_bots[bot.self_id] = AyakaBot(bot)