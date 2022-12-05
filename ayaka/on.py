# '''注册回调'''
# import asyncio
# import datetime
# from typing import Callable, Coroutine, TYPE_CHECKING, Union, List
# from loguru import logger
# from .config import INIT_STATE, ayaka_root_config

# if TYPE_CHECKING:
#     from .ayaka import AyakaApp


# class AyakaOn:
#     def __init__(self, app: "AyakaApp") -> None:
#         self.app = app

#     def everyday(self, h: int, m: int, s: int):
#         '''每日定时触发'''
#         return self.interval(86400, h, m, s)

#     def interval(self, gap: int, h=-1, m=-1, s=-1):
#         '''在指定的时间点后循环触发'''
#         return self.on_timer(gap, h, m, s)

#     def state(self, *states: str):
#         '''注册有状态回调'''
#         if not states:
#             states = INIT_STATE

#         def decorator(func):
#             # 取出之前存的参数
#             return self.on_handle(func.cmds, states, False)(func)
#         return decorator

#     def idle(self, super=False):
#         '''注册无状态回调'''
#         def decorator(func):
#             # 取出之前存的参数
#             return self.on_handle(func.cmds, None, super)(func)
#         return decorator

#     def command(self, *cmds: str):
#         def decorator(func):
#             func.cmds = cmds
#             return func
#         return decorator

#     def text(self):
#         def decorator(func):
#             func.cmds = ""
#             return func
#         return decorator

#     def on_handle(self, cmds: Union[List[str], str], states: Union[List[str], str], super: bool):
#         '''注册'''
#         cmds = ensure_list(cmds)
#         states = ensure_list(states)

#         def decorator(func: Callable[[], Coroutine]):
#             for state in states:
#                 for cmd in cmds:
#                     t = AyakaTrigger(self.app.name, cmd, state, super, func)
#                     self.app.triggers.append(t)

#                 # 如果有帮助，自动添加到_help中
#                 doc = func.__doc__
#                 if doc:
#                     if state is None:
#                         state = INIT_STATE
#                     if state not in self.app._help:
#                         self.app._help[state] = []
#                     cmd_str = '/'.join(cmds)
#                     if not cmd_str:
#                         cmd_str = "*"
#                     self.app._help[state].append(f"- {cmd_str} {doc}")

#             return func
#         return decorator

#     def on_timer(self, gap: int, h: int, m: int, s: int):
#         '''在指定的时间点后循环触发'''
#         def decorator(func):
#             t = AyakaTimer(self.app.name, gap, h, m, s, func)
#             self.app.timers.append(t)
#             return func
#         return decorator


# class AyakaTrigger:
#     def __repr__(self) -> str:
#         return f"AyakaTrigger({self.app_name}, {self.cmd}, {self.state}, {self.super}, {self.func.__name__})"

#     def __init__(self, app_name, cmd, state, super, func) -> None:
#         self.app_name = app_name
#         self.cmd = cmd
#         self.state = state
#         self.super = super
#         self.func = func
#         if ayaka_root_config.debug:
#             print(self)

#     async def run(self):
#         # 日志记录
#         items = []

#         if self.cmd:
#             items.append("<y>命令</y>")
#         else:
#             items.append("<g>消息</g>")

#         app_name = f"<y>{self.app_name}</y>"
#         if self.state is not None:
#             app_name += f" <g>{self.state}</g>"
#         items.append(app_name)

#         if self.cmd:
#             items.append(f"<y>{self.cmd}</y>")

#         items.append(f"执行回调 <c>{self.func.__name__}</c>")
#         info = " | ".join(items)
#         logger.opt(colors=True).debug(info)

#         # 运行回调
#         await self.func()


# class AyakaTimer:
#     def __repr__(self) -> str:
#         return f"AyakaTimer({self.name}, {self.gap}, {self.func.__name__})"

#     def __init__(self, name: str, gap: int, h: int, m: int, s: int, func) -> None:
#         self.name = name
#         self.h = h
#         self.m = m
#         self.s = s
#         self.gap = gap
#         self.func = func
#         if ayaka_root_config.debug:
#             print(self)

#     def start(self):
#         asyncio.create_task(self.run_forever())

#     async def run_forever(self):
#         # 有启动时间点要求的
#         time_i = int(datetime.datetime.now().timestamp())
#         if self.h >= 0:
#             _time_i = self.h*3600+self.m*60+self.s
#             # 移除时区偏差
#             time_i -= 57600
#             gap = 86400 - (time_i - _time_i) % 86400
#             await asyncio.sleep(gap)
#         elif self.m >= 0:
#             _time_i = self.m*60+self.s
#             gap = 3600 - (time_i-_time_i) % 3600
#             await asyncio.sleep(gap)
#         elif self.s >= 0:
#             _time_i = self.s
#             gap = 60 - (time_i-_time_i) % 60
#             await asyncio.sleep(gap)

#         while True:
#             logger.opt(colors=True).debug(f"触发定时任务 <y>{self.name}</y>")
#             asyncio.create_task(self.func())
#             await asyncio.sleep(self.gap)


# def ensure_list(items):
#     if isinstance(items, tuple):
#         return [item for item in items]
#     if not isinstance(items, list):
#         return [items]
#     return items
