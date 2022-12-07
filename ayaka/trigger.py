import inspect
from typing import TYPE_CHECKING, Awaitable, Callable, List, Literal, Union
from pydantic import ValidationError

from .input import AyakaInput
from .config import ayaka_root_config
from .cache import AyakaCache

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
            if issubclass(cls, AyakaInput):
                try:
                    params[k] = cls(self.app.args)
                except ValidationError as e:
                    await self.app.bot.send_group_msg(group_id=self.app.group_id, message=str(e))
                    return
            elif issubclass(cls, AyakaCache):
                cache = self.app.cache
                name = cls.__name__
                if name not in cache:
                    cache[name] = cls()
                params[k] = cache[name]
            else:
                # [-]
                # 不断更新
                pass

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
