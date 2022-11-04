from typing import List, Dict, TYPE_CHECKING
from pathlib import Path
from .storage import AyakaPath
from .config import AYAKA_DEBUG
from .constant import app_list, group_list
from .cache import AyakaCache

if TYPE_CHECKING:
    from .ayaka import AyakaApp


class AyakaGroup:
    def __repr__(self) -> str:
        return f"AyakaGroup({self.bot_id}, {self.group_id}, {self.apps})"

    def forbid_init(self):
        names = [
            "data", "groups",
            self.bot_id,
            self.group_id
        ]
        names = [str(name) for name in names]
        path = Path(*names)
        self.store_forbid = AyakaPath(path).json("forbid", [])

    def forbid_load(self):
        return self.store_forbid.load()

    def forbid_save(self, data):
        return self.store_forbid.save(data)

    def __init__(self, bot_id: int, group_id: int) -> None:
        self.bot_id = bot_id
        self.group_id = group_id
        self.running_app: "AyakaApp" = None

        # 读取forbit列表
        self.forbid_init()
        forbid_names = self.forbid_load()

        # 添加app，并分配独立数据空间
        self.apps: List["AyakaApp"] = []
        self.cache_dict: Dict[str, AyakaCache] = {}
        for app in app_list:
            if app.name not in forbid_names:
                self.apps.append(app)
                self.cache_dict[app.name] = AyakaCache()

        group_list.append(self)

        if AYAKA_DEBUG:
            print(self)

    @property
    def running_app_name(self):
        if self.running_app:
            return self.running_app.name
        return ""

    def get_app(self, name: str):
        '''根据app名获取该group所启用的app，不存在则返回None'''
        for app in self.apps:
            if app.name == name:
                return app

    def permit_app(self, name: str):
        '''启用指定app'''
        if self.get_app(name):
            return True

        for app in app_list:
            if app.name == name:
                self.apps.append(app)
                # 从forbit列表移除
                app_names: list = self.forbid_load()
                if name in app_names:
                    app_names.remove(name)
                    self.forbid_save(app_names)
                return True

    def forbid_app(self, name: str):
        '''禁用指定app'''
        if name == "ayaka_master":
            return

        app = self.get_app(name)
        if not app:
            return

        # 禁用正在运行的应用
        if self.running_app_name == name:
            self.running_app = None

        # 移除
        self.apps.remove(app)

        # 添加到forbit列表
        app_names: list = self.forbid_load()
        if name not in app_names:
            app_names.append(name)
            self.forbid_save(app_names)
        return True
