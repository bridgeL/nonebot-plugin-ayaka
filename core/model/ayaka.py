from typing import List
from .bot import AyakaBot
from ...adapter import Bot


class Ayaka:
    def __init__(self) -> None:
        self.ayaka_bots: List[AyakaBot] = []

    def get_abot(self, bot_id: str):
        for abot in self.ayaka_bots:
            if abot.bot.self_id == bot_id:
                return abot

    def add(self, bot: Bot):
        if not self.get_abot(bot.self_id):
            self.ayaka_bots.append(AyakaBot(bot))
