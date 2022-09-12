from ayaka.logger import logger


class Trigger:
    def __init__(self, app_name, cmd, state, super, group, private, func) -> None:
        self.app_name = app_name
        self.cmd = cmd
        self.state = state
        self.super = super
        self.group = group
        self.private = private
        self.func = func

    async def run(self):
        state = self.state if self.state else ""
        cmd = self.cmd if self.cmd else ""

        logger.info(
            f"触发Ayaka应用[<y>{self.app_name}</y>{'|' if state else ''}<g>{state}</g>] <y>{cmd}</y>")
        await self.func()
