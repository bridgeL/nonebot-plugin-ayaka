from typing import TYPE_CHECKING
from ...adapter import logger

if TYPE_CHECKING:
    from .plugin import AyakaApp


class AyakaTrigger:
    def __init__(self, app: "AyakaApp", cmd: str, state: str, super: bool, group: bool, private: bool, func) -> None:
        self.app = app
        self.cmd = cmd
        self.state = state
        self.super = super
        self.group = group
        self.private = private
        self.func = func

    async def run(self):
        # 上 下 文 切 换
        self.app.switch()

        state = self.state if self.state else ""
        cmd = self.cmd if self.cmd else ""

        logger.info(
            f"触发Ayaka应用[<y>{self.app.name}</y>{'|' if state else ''}<g>{state}</g>] <y>{cmd}</y>")
        await self.func()
