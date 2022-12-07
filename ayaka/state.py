from enum import Enum
import inspect
from typing import Awaitable, Callable, List, Literal, Union
from typing_extensions import Self
from pydantic import BaseModel, ValidationError

from .ayaka_input import AyakaInputModel
from .config import ayaka_root_config
from .constant import _enter_exit_during, _args, _bot, _group
from .ayaka_chain import AyakaChainNode


def add_flag():
    _enter_exit_during.set(_enter_exit_during.get()+1)


def sub_flag():
    _enter_exit_during.set(_enter_exit_during.get()-1)


class AyakaTrigger(BaseModel):
    app_name: str
    cmds: List[str]
    func: Callable[..., Awaitable]
    deep: Union[int, Literal["all"]]
    block: bool

    def __init__(self, func, cmds, deep, app_name, block):
        super().__init__(
            func=func, cmds=cmds, deep=deep,
            app_name=app_name, block=block
        )
        if ayaka_root_config.debug:
            print(repr(self))

    async def run(self):
        sig = inspect.signature(self.func)
        model = None
        for k, v in sig.parameters.items():
            cls = v.annotation
            if issubclass(cls, AyakaInputModel):
                model = [k, cls]
                break

        if not model:
            await self.func()

        k, cls = model
        args = _args.get()
        try:
            data = cls(args)
        except ValidationError as e:
            bot = _bot.get()
            group = _group.get()
            await bot.send_group_msg(group_id=group.group_id, message=str(e))
            return

        await self.func(**{k: data})

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self})"

    def __str__(self) -> str:
        data = self.dict()
        data["func"] = self.func.__name__
        return " ".join(f"{k}={v}" for k, v in data.items())


class AyakaStateBase(Enum):
    CURRENT = "current"
    PLUGIN = "plugin"
    ROOT = "root"


class AyakaState(AyakaChainNode):
    def __init__(self, key="root", parent: Self = None):
        super().__init__(key, parent)
        self.enter_funcs = []
        self.exit_funcs = []
        self.triggers: List[AyakaTrigger] = []

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

    def on_cmd(self, *cmds: str, app_name: str, deep: Union[int, Literal["all"]] = 0, block=True):
        def decorator(func):
            t = AyakaTrigger(func, cmds, deep, app_name, block)
            self.triggers.append(t)
            return func
        return decorator

    def on_text(self, app_name: str, deep: Union[int, Literal["all"]] = 0, block=True):
        return self.on_cmd(app_name=app_name, deep=deep, block=block)


root_state = AyakaState()
