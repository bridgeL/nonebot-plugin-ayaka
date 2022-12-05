from typing import List, Literal, Union


class AyakaTrigger:
    def __init__(self, func, cmds: List[str], deep: Union[int, Literal["any"]], app_name: str, block: bool) -> None:
        self.func = func
        self.deep = deep
        self.cmds = cmds
        self.app_name = app_name
        self.block = block

    async def run(self):
        await self.func()


class AyakaState:
    def __init__(self, key: str = "root", parent: "AyakaState" = None):
        self.key = key
        self.parent = parent
        if not parent:
            self.keys = [key]
        else:
            self.keys = [*parent.keys, key]
        self.children: List["AyakaState"] = []

        self.enter_funcs = []
        self.exit_funcs = []
        self.triggers: List[AyakaTrigger] = []

    def __getitem__(self, k):
        for state in self.children:
            if state.key == k:
                return state
        state = AyakaState(k, self)
        self.children.append(state)
        return state

    def __getattr__(self, k):
        return self[k]

    def __str__(self) -> str:
        return ".".join(self.keys)

    def __repr__(self) -> str:
        return str(self)

    async def enter(self):
        print(">>>", self.key)
        for func in self.enter_funcs:
            await func()

    async def exit(self):
        print("<<<", self.key)
        for func in self.exit_funcs:
            await func()

    def on_enter(self, func):
        self.enter_funcs.append(func)
        return func

    def on_exit(self, func):
        self.exit_funcs.append(func)
        return func

    def on_cmd(self, cmds: List[str], app_name: str, deep: Union[int, Literal["any"]] = 0, block=True):
        def decorator(func):
            t = AyakaTrigger(func, cmds, deep, app_name, block)
            self.triggers.append(t)
            return func
        return decorator

    def on_text(self, app_name: str, deep: Union[int, Literal["any"]] = 0, block=True):
        return self.on_cmd([], app_name, deep, block)

    def dict(self):
        if not self.children:
            return
        return {child.key: child.dict() for child in self.children}


root_state = AyakaState()
