from ..adapter import Bot, on_connect
from .model import Ayaka


ayaka = Ayaka()


@on_connect
async def add_ayakabot(bot: Bot):
    ayaka.add(bot)
