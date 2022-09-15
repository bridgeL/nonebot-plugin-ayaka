from typing import TYPE_CHECKING, List, Set
from .plugin import AyakaApp, prototype_apps

if TYPE_CHECKING:
    from .bot import AyakaBot


class AyakaDevice:
    def __init__(self, abot: "AyakaBot", device_id: int, group: bool) -> None:
        self.abot: "AyakaBot" = abot
        self.group = group
        self.device_id = device_id
        self.running_app: AyakaApp = None
        self.listeners: Set[AyakaDevice] = set()
        self.apps: List[AyakaApp] = []

        # 从原型生成
        for app in prototype_apps:
            if (app.group and group) or (app.private and not group):
                self.apps.append(app.clone(self, abot))

    async def add_listener(self, device_id: int):
        dev = await self.abot.get_device(device_id)
        if dev:
            self.listeners.add(dev)

    async def remove_listener(self, device_id: int):
        for dev in self.listeners:
            if dev.device_id == device_id:
                self.listeners.remove(dev)
                return

    def start_app(self, app: AyakaApp, state: str):
        '''返回提示信息，state为进入app后的初始状态'''
        if self.running_app:
            return False, f"设备正被应用[{self.running_app.name}]占用"

        if not app.valid:
            return False, f"设备已禁用此应用[{app.name}]，请联系管理员开启"

        self.running_app = app
        app.state = state
        return True, f"设备已开启应用[{app.name}]"

    def close_app(self):
        if not self.running_app:
            return False, f"设备当前没有应用在运行"
        name = self.running_app.name
        self.running_app = None
        return True, f"设备已关闭应用[{name}]"

    def get_app(self, app_name: str):
        for app in self.apps:
            if app.name == app_name:
                return app

    def reboot(self):
        self.running_app = None
        self.listeners = set()
        self.apps: List[AyakaApp] = []

        # 从原型生成
        for app in prototype_apps:
            if (app.group and self.group) or (app.private and not self.group):
                self.apps.append(app.clone(self, self.abot))
