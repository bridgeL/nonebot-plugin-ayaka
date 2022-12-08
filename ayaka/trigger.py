import inspect
from typing import TYPE_CHECKING, Awaitable, Callable, List, Literal, Union
from .depend import AyakaDepend
from .config import ayaka_root_config

if TYPE_CHECKING:
    from .ayaka import AyakaApp


class AyakaTrigger:
    def __init__(self, func: Callable[..., Awaitable], cmds: List[str], deep: Union[int, Literal["all"]], app: "AyakaApp", block: bool):
        self.func = func
        self.cmds = cmds
        self.deep = deep
        self.app = app
        self.block = block

        if ayaka_root_config.debug:
            print(repr(self))

    async def run(self):
        params = {}
        sig = inspect.signature(self.func)

        for k, v in sig.parameters.items():
            cls = v.annotation
            if issubclass(cls, AyakaDepend):
                d = await cls.create(app=self.app)
                if not d:
                    return
                params[k] = d

        await self.func(**params)

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
