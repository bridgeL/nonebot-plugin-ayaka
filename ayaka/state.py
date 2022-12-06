from enum import Enum
from typing import Awaitable, Callable, List, Literal, Optional, Type, Union
from typing_extensions import Self
from pydantic import BaseModel

from .ayaka_input import AyakaInputModel
from .config import ayaka_root_config
from .constant import _enter_exit_during
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
    model: Optional[Type[AyakaInputModel]]

    def __init__(self, func, cmds, deep, app_name, block, model):
        super().__init__(
            func=func, cmds=cmds, deep=deep,
            app_name=app_name, block=block, model=model
        )
        if ayaka_root_config.debug:
            print(repr(self))

    async def run(self):
        await self.func()

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

    def on_cmd(self, *cmds: str, app_name: str, deep: Union[int, Literal["all"]] = 0, block=True, model: Type[AyakaInputModel] = None):
        def decorator(func):
            t = AyakaTrigger(func, cmds, deep, app_name, block, model)
            self.triggers.append(t)
            return func
        return decorator

    def on_text(self, app_name: str, deep: Union[int, Literal["all"]] = 0, block=True, model: Type[AyakaInputModel] = None):
        return self.on_cmd(app_name=app_name, deep=deep, block=block, model=model)


root_state = AyakaState()
