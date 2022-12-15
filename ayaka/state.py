import inspect
from typing import TYPE_CHECKING, List, Literal, Union, Awaitable, Callable
from typing_extensions import Self
import asyncio
import datetime
from loguru import logger

from .config import ayaka_root_config
from .constant import _enter_exit_during
from .depend import AyakaDepend, AyakaInput


if TYPE_CHECKING:
    from .ayaka import AyakaApp


def add_flag():
    _enter_exit_during.set(_enter_exit_during.get()+1)


def sub_flag():
    _enter_exit_during.set(_enter_exit_during.get()-1)


class AyakaState:
    def __init__(self, key="root", parent: Self = None):
        self.key = key
        self.parent = parent
        if not parent:
            self.keys = [key]
        else:
            self.keys = [*parent.keys, key]
        self.children: List[Self] = []

        self.enter_funcs = []
        self.exit_funcs = []
        self.triggers: List[AyakaTrigger] = []

    def __getitem__(self, k):
        if isinstance(k, slice):
            s = AyakaState("")
            s.keys = self.keys[k]
            if s.keys:
                s.key = s.keys[-1]
            return s

        if isinstance(k, int):
            s = AyakaState(self.keys[k])
            return s

        for node in self.children:
            if node.key == k:
                return node
        node = self.__class__(k, self)
        self.children.append(node)
        return node

    def __getattr__(self, k: str):
        return self[k]

    def __iter__(self):
        return iter(self.children)

    def __str__(self) -> str:
        return ".".join(self.keys)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self})"

    def join(self, *keys: str) -> Self:
        node = self
        for key in keys:
            node = node[key]
        return node

    def belong(self, node: Self):
        if len(self.keys) < len(node.keys):
            return False

        for i in range(len(node.keys)):
            if node.keys[i] != self.keys[i]:
                return False

        return True

    def __ge__(self, node: Self):
        return self.belong(node)

    def __le__(self, node: Self):
        return node.belong(self)

    def __gt__(self, node: Self):
        return self >= node and len(self.keys) > len(node.keys)

    def __lt__(self, node: Self):
        return self <= node and len(self.keys) < len(node.keys)

    def __eq__(self, node: Self):
        return self <= node and len(self.keys) == len(node.keys)

    def dict(self):
        data = [child.dict() for child in self.children]
        return {
            "name": self.key,
            "triggers": self.triggers,
            "children": data,
        }

    async def enter(self):
        if ayaka_root_config.debug:
            print(">>>", self.key)
        add_flag()
        for func in self.enter_funcs:
            await func()
        sub_flag()

    async def exit(self):
        if ayaka_root_config.debug:
            print("<<<", self.key)
        add_flag()
        for func in self.exit_funcs:
            await func()
        sub_flag()

    def on_enter(self):
        def decorator(func):
            self.enter_funcs.append(func)
            return func
        return decorator

    def on_exit(self):
        def decorator(func):
            self.exit_funcs.append(func)
            return func
        return decorator

    def on_cmd(self, cmds: List[str], app: "AyakaApp", deep: Union[int, Literal["all"]] = 0, block=True):
        def decorator(func):
            t = AyakaTrigger(func, cmds, deep, app, block, self)
            self.triggers.append(t)
            return func
        return decorator

    def on_text(self, app: "AyakaApp", deep: Union[int, Literal["all"]] = 0, block=True):
        return self.on_cmd([], app, deep, block)


class AyakaTrigger:
    def __init__(self, func: Callable[..., Awaitable], cmds: List[str], deep: Union[int, Literal["all"]], app: "AyakaApp", block: bool, state: AyakaState):
        self.func = func
        self.cmds = cmds
        self.deep = deep
        self.app = app
        self.block = block
        self.state = state

        # 默认没有解析模型
        models: List[AyakaInput] = []
        sig = inspect.signature(func)
        for k, v in sig.parameters.items():
            cls = v.annotation
            if issubclass(cls, AyakaInput):
                models.append(cls)

        # 生成帮助
        doc = "" if not func.__doc__ else f"| {func.__doc__}"
        cmd_str = '/'.join(cmds) if cmds else "<任意文字>"

        if not models:
            help = f"- {cmd_str} {doc}"
        else:
            helps = []
            for model in models:
                data = model.help()
                keys_str = " ".join(f"<{k}>" for k in data.keys())
                data_str = "\n".join(f"    <{k}> {v}" for k, v in data.items())
                helps.append(f"- {cmd_str} {keys_str} {doc}\n{data_str}")
            help = "\n".join(helps)

        self.help = help
        if len(state.keys) > 1:
            s = str(state[1:])
            if s not in self.app.state_helps:
                self.app.state_helps[s] = []
            self.app.state_helps[s].append(help)
        else:
            self.app.idle_helps.append(help)

        if ayaka_root_config.debug:
            print(repr(self))

    async def run(self):
        params = {}
        sig = inspect.signature(self.func)

        for k, v in sig.parameters.items():
            cls = v.annotation
            if issubclass(cls, AyakaDepend):
                d = await cls.create_by_app(self.app)
                if not d:
                    return False
                params[k] = d

        await self.func(**params)
        return True

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self})"

    def __str__(self) -> str:
        data = {
            "func": self.func.__name__,
            "app_name": self.app.name,
            "cmds": self.cmds,
            "deep": self.deep,
            "block": self.block
        }
        return " ".join(f"{k}={v}" for k, v in data.items())


class AyakaTimer:
    def __repr__(self) -> str:
        return f"AyakaTimer({self.app.name}, {self.gap}, {self.func.__name__})"

    def __init__(self,  app: "AyakaApp", gap: int, h: int, m: int, s: int, func, show=True) -> None:
        self.app = app
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
                    f"定时任务 | 插件：<y>{self.app.name}</y> | 回调：<c>{self.func.__name__}</c>")
            asyncio.create_task(self.func())
            await asyncio.sleep(self.gap)


root_state = AyakaState()
