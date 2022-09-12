from typing import TYPE_CHECKING, Dict, List

from .trigger import Trigger
from .plugin import AyakaApp, prototype_apps

if TYPE_CHECKING:
    from .bot import AyakaBot


class AyakaDevice:
    def __init__(self, abot: "AyakaBot", device_id: int, group: bool) -> None:
        self.running_app_name = ""
        self.device_id = device_id
        self.group = group
        self.listeners = set()

        self.apps: Dict[str, AyakaApp] = {}

        # 从原型生成
        for app in prototype_apps:
            if (app.group and group) or (app.private and not group):
                self.apps[app.name] = app.clone(self, abot)


    def add_listener(self, device_id: int):
        self.listeners.add(device_id)

    def remove_listener(self, device_id: int):
        if device_id in self.listeners:
            self.listeners.remove(device_id)

    def start_app(self, app_name: str, state: str):
        '''返回提示信息，state为进入app后的初始状态'''
        if self.running_app_name:
            return False, f"设备{self.device_id} 正被应用[{self.running_app_name}]占用"

        if not self.apps[app_name].valid:
            return False, f"该设备[{self.device_id}]已禁用此应用[{app_name}]，请联系管理员开启"

        self.running_app_name = app_name
        self.apps[app_name].state = state
        return True, f"设备{self.device_id} 已开启应用[{app_name}]"

    def close_app(self):
        if not self.running_app_name:
            return False, f"设备{self.device_id} 当前没有应用在运行"
        name = self.running_app_name
        self.running_app_name = ""
        return True, f"设备{self.device_id} 已关闭应用[{name}]"

    def get_app(self, app_name: str):
        return self.apps.get(app_name, None)

    def get_running_app(self):
        return self.get_app(self.running_app_name)
