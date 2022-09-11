from typing import List
from .device import AyakaDevice
from nonebot.adapters.onebot.v11 import Bot


class AyakaBot:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.devices: List[AyakaDevice] = []

    async def get_device(self, device_id: int):
        for d in self.devices:
            if d.device_id == device_id:
                return d

        # 自动增加
        data = await self.bot.get_group_list()
        for d in data:
            if device_id == d["group_id"]:
                d = AyakaDevice(self, device_id, True)
                self.devices.append(d)
                return d

        data = await self.bot.get_friend_list()
        for d in data:
            if device_id == d["user_id"]:
                d = AyakaDevice(self, device_id, False)
                self.devices.append(d)
                return d

    async def is_friend(self, uid: int):
        data = await self.bot.get_friend_list()
        for d in data:
            if uid == d["user_id"]:
                return True
        return False
