'''注册回调[旧API]'''
import asyncio
import datetime
from typing import TYPE_CHECKING
from loguru import logger
from .config import ayaka_root_config
from .state import root_state

if TYPE_CHECKING:
    from .ayaka import AyakaApp


class AyakaOn:
    def __init__(self, app: "AyakaApp") -> None:
        self.app = app

    def state(self, *states: str):
        '''注册有状态回调'''
        if "*" in str(states):
            def decorator(func):
                func = self.app.on_deep_all("all")(func)
                func = self.app.on_state()(func)
                return func
            return decorator
        states = [s.split(".") for s in states]
        return self.app.on_state(*states)

    def idle(self, super=False):
        '''注册无状态回调'''
        if super:
            def decorator(func):
                func = self.app.on_state(root_state)(func)
                func = self.app.on_deep_all("all")(func)
                return func
            return decorator
        return self.app.on_state(root_state)

    def command(self, *cmds: str):
        return self.app.on_cmd(*cmds)

    def text(self):
        return self.app.on_no_block()

    def everyday(self, h: int, m: int, s: int):
        '''每日定时触发'''
        return self.interval(86400, h, m, s)

    def interval(self, gap: int, h=-1, m=-1, s=-1, show=True):
        '''在指定的时间点后循环触发'''
        return self.on_timer(gap, h, m, s, show)

    def on_timer(self, gap: int, h: int, m: int, s: int, show=True):
        '''在指定的时间点后循环触发'''
        def decorator(func):
            t = AyakaTimer(self.app.name, gap, h, m, s, func, show)
            self.app.timers.append(t)
            return func
        return decorator


class AyakaTimer:
    def __repr__(self) -> str:
        return f"AyakaTimer({self.name}, {self.gap}, {self.func.__name__})"

    def __init__(self, name: str, gap: int, h: int, m: int, s: int, func, show=True) -> None:
        self.name = name
        self.h = h
        self.m = m
        self.s = s
        self.gap = gap
        self.func = func
        self.show = show
        if ayaka_root_config.debug:
            print(self)

    def start(self):
        asyncio.create_task(self.run_forever())

    async def run_forever(self):
        # 有启动时间点要求的
        time_i = int(datetime.datetime.now().timestamp())
        if self.h >= 0:
            _time_i = self.h*3600+self.m*60+self.s
            # 移除时区偏差
            time_i -= 57600
            gap = 86400 - (time_i - _time_i) % 86400
            await asyncio.sleep(gap)
        elif self.m >= 0:
            _time_i = self.m*60+self.s
            gap = 3600 - (time_i-_time_i) % 3600
            await asyncio.sleep(gap)
        elif self.s >= 0:
            _time_i = self.s
            gap = 60 - (time_i-_time_i) % 60
            await asyncio.sleep(gap)

        while True:
            if self.show:
                logger.opt(colors=True).debug(
                    f"定时任务 | 插件：<y>{self.name}</y> | 回调：<c>{self.func.__name__}</c>")
            asyncio.create_task(self.func())
            await asyncio.sleep(self.gap)
