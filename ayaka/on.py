'''注册回调[旧API]'''
from typing import TYPE_CHECKING
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
                func = self.app.on_state()(func)
                func = self.app.on_deep_all()(func)
                return func
            return decorator
        return self.app.on_state(*states)

    def idle(self, super=False):
        '''注册无状态回调'''
        if super:
            def decorator(func):
                func = self.app.on_state(root_state)(func)
                func = self.app.on_deep_all()(func)
                return func
            return decorator
        return self.app.on_state(root_state)

    def command(self, *cmds: str):
        return self.app.on_cmd(*cmds)

    def text(self):
        return self.app.on_text()

    def everyday(self, h: int, m: int, s: int):
        '''每日定时触发'''
        return self.app.on_everyday(86400, h, m, s)

    def interval(self, gap: int, h=-1, m=-1, s=-1, show=True):
        '''在指定的时间点后循环触发'''
        return self.app.on_interval(gap, h, m, s, show)

    def on_timer(self, gap: int, h: int, m: int, s: int, show=True):
        '''在指定的时间点后循环触发'''
        return self.app.on_interval(gap, h, m, s, show)

