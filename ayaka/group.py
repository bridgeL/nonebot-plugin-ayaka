'''群组'''
from typing import List, Dict, TYPE_CHECKING
from loguru import logger

from .depend import AyakaCache
from .config import ayaka_root_config
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

    def __init__(self, bot_id: int, group_id: int) -> None:
        self.bot_id = bot_id
        self.group_id = group_id
        self.state = root_state

        # 添加app，并分配独立数据空间
        self.apps: List["AyakaApp"] = []
        self.cache_dict: Dict[str, Dict[str, AyakaCache]] = {}
        for app in app_list:
            # if app.name not in forbid_names:
            self.apps.append(app)
            self.cache_dict[app.name] = {}

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
