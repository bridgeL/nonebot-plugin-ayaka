import inspect
from typing import TYPE_CHECKING, List, Literal, Union, Awaitable, Callable
from typing_extensions import Self

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

    def __gt__(self, node: Self):
        return self >= node and len(self.keys) > len(node.keys)

    def __ge__(self, node: Self):
        return self.belong(node)

    def __lt__(self, node: Self):
        return self <= node and len(self.keys) < len(node.keys)

    def __le__(self, node: Self):
        return node.belong(self)

    def __eq__(self, node: Self):
        return self <= node and len(self.keys) == len(node.keys)

    def belong(self, node: Self):
        if len(self.keys) < len(node.keys):
            return False

        for i in range(len(node.keys)):
            if node.keys[i] != self.keys[i]:
                return False

        return True

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

    def on_cmd(self, *cmds: str, app: "AyakaApp", deep: Union[int, Literal["all"]] = 0, block=True):
        def decorator(func):
            t = AyakaTrigger(func, cmds, deep, app, block, self)
            self.triggers.append(t)
            return func
        return decorator

    def on_text(self, app: "AyakaApp", deep: Union[int, Literal["all"]] = 0, block=True):
        return self.on_cmd(app=app, deep=deep, block=block)


class AyakaTrigger:
    def __init__(self, func: Callable[..., Awaitable], cmds: List[str], deep: Union[int, Literal["all"]], app: "AyakaApp", block: bool, state: AyakaState):
        self.func = func
        self.cmds = cmds
        self.deep = deep
        self.app = app
        self.block = block
        self.state = state

        # 默认没有解析模型
        model = None
        sig = inspect.signature(func)
        for k, v in sig.parameters.items():
            cls = v.annotation
            if issubclass(cls, AyakaInput):
                model = cls
                break
        self.model = model

        # 生成帮助
        doc = "" if not func.__doc__ else f"| {func.__doc__}"
        cmd_str = '/'.join(cmds) if cmds else "<任意文字>"

        if not model:
            help = f"- {cmd_str} {doc}"
        else:
            data = model.help()
            keys_str = " ".join(f"<{k}>" for k in data.keys())
            data_str = "\n".join(f"    <{k}> {v}" for k, v in data.items())
            help = f"- {cmd_str} {keys_str} {doc}\n{data_str}"

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
                d = await cls._create_by_app(self.app)
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


root_state = AyakaState()
