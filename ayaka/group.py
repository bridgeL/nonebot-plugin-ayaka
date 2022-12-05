'''群组'''
from typing import List, Dict, TYPE_CHECKING
from pathlib import Path
from loguru import logger
from .config import ayaka_root_config
from .storage import AyakaPath
from .cache import AyakaCacheCtrl
from .state import root_state, AyakaState
from .constant import app_list, group_list, _enter_exit_during

if TYPE_CHECKING:
    from .ayaka import AyakaApp


def get_group(bot_id: int, group_id: int):
    '''获取对应的AyakaGroup对象，自动增加'''
    for group in group_list:
        if group.bot_id == bot_id and group.group_id == group_id:
            break
    else:
        group = AyakaGroup(bot_id, group_id)
    return group


class AyakaGroup:
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.bot_id}, {self.group_id}, {self.apps})"

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
        self.state = root_state

        # # 读取forbit列表
        # self.forbid_init()
        # forbid_names = self.forbid_load()

        # 添加app，并分配独立数据空间
        self.apps: List["AyakaApp"] = []
        self.cache_dict: Dict[str, AyakaCacheCtrl] = {}
        for app in app_list:
            # if app.name not in forbid_names:
            if 1:
                self.apps.append(app)
                self.cache_dict[app.name] = AyakaCacheCtrl()

        group_list.append(self)

        if ayaka_root_config.debug:
            print(self)

    async def back(self):
        if self.state.parent:
            await self.state.exit()
            self.state = self.state.parent
            return self.state

    async def goto(self, state: AyakaState):
        if _enter_exit_during.get() > 0:
            logger.warning("你正在AyakaState的enter/exit方法中进行状态转移，这可能会导致无法预料的错误")

        keys = state.keys

        # 找到第一个不同的结点
        n0 = len(keys)
        n1 = len(self.state.keys)
        n = min(n0, n1)
        for i in range(n):
            if keys[i] != self.state.keys[i]:
                break
        else:
            i += 1

        # 回退
        for j in range(i, n1):
            await self.back()
        keys = keys[i:]

        # 重新出发
        for key in keys:
            self.state = self.state[key]
            await self.state.enter()
        logger.opt(colors=True).debug(f"状态：<c>{self.state}</c>")
        return self.state

    def get_app(self, name: str):
        '''根据app名获取该group所启用的app，不存在则返回None'''
        for app in self.apps:
            if app.name == name:
                return app

    # def permit_app(self, name: str):
    #     '''启用指定app'''
    #     if self.get_app(name):
    #         return True

    #     for app in app_list:
    #         if app.name == name:
    #             self.apps.append(app)
    #             # 从forbit列表移除
    #             app_names: list = self.forbid_load()
    #             if name in app_names:
    #                 app_names.remove(name)
    #                 self.forbid_save(app_names)
    #             return True

    # def forbid_app(self, name: str):
    #     '''禁用指定app'''
    #     if name == "ayaka_master":
    #         return

    #     app = self.get_app(name)
    #     if not app:
    #         return

    #     # 禁用正在运行的应用
    #     if self.running_app_name == name:
    #         self.running_app = None

    #     # 移除
    #     self.apps.remove(app)

    #     # 添加到forbit列表
    #     app_names: list = self.forbid_load()
    #     if name not in app_names:
    #         app_names.append(name)
    #         self.forbid_save(app_names)
    #     return True
