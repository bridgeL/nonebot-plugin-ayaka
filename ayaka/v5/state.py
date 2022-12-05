from typing import List, Literal, Union
from ayaka.driver import Message, MessageSegment

prefix = ""
sep = " "


def get_cmd(message: Message):
    '''返回命令'''
    first = ""
    for m in message:
        if m.type == "text":
            first += str(m)
        else:
            break
    if not first or not first.startswith(prefix):
        return ""
    first += sep
    return first.split(sep, 1)[0][len(prefix):]


def divide_message(message: Message):
    args: List[MessageSegment] = []

    for m in message:
        if m.is_text():
            ss = str(m).split(sep)
            args.extend(MessageSegment.text(s) for s in ss if s)
        else:
            args.append(m)

    return args


def remove_cmd(cmd: str, message: Message):
    m = message[0]
    if m.is_text():
        m_str = str(m)
        m_str = m_str[len(prefix+cmd):].lstrip(sep)
        if not m_str:
            return message[1:]
        return [MessageSegment.text(m_str)] + message[1:]
    return message


class AyakaFunc:
    def __init__(self, func, cmds: list, deep: Union[int, Literal["any"]]) -> None:
        self.func = func
        self.deep = deep
        self.cmds = cmds


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
        self.msg_funcs: List[AyakaFunc] = []

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

    def enter(self):
        print(">>>", self.key)
        for func in self.enter_funcs:
            func()

    def exit(self):
        print("<<<", self.key)
        for func in self.exit_funcs:
            func()

    def deal_msg(self, msg):
        # []
        pass

    def on_enter(self, func):
        self.enter_funcs.append(func)
        return func

    def on_exit(self, func):
        self.exit_funcs.append(func)
        return func

    def on_cmd(self, cmds: List[str], deep: Union[int, Literal["any"]] = 0):
        def decorator(func):
            self.msg_funcs.append(AyakaFunc(func, cmds, deep))
            return func
        return decorator

    def on_text(self, deep: Union[int, Literal["any"]] = 0):
        return self.on_cmd(cmds=[], deep=deep)

    def dict(self):
        if not self.children:
            return
        return {child.key: child.dict() for child in self.children}


root_state = AyakaState()


class AyakaGroup:
    def __init__(self) -> None:
        self.state = root_state


group = AyakaGroup()


class AyakaApp:
    def __init__(self, name) -> None:
        self.name = name
        self.group = group

    @property
    def state(self):
        return self.group.state

    def _ensure_state(self, state: Union[AyakaState, str, List[str]]):
        if isinstance(state, str):
            state = self.get_state(state)
        if isinstance(state, list):
            state = self.get_state(*state)
        return state

    @state.setter
    def state(self, state: Union[AyakaState, str, List[str]]):
        state = self._ensure_state(state)
        return self.goto(state)

    def get_state(self, *keys: str, from_: Literal["current", "plugin", "root"] = "plugin"):
        '''
            假设当前状态为 root.test.a

            - 基于 当前状态

            >>> get_state(key1, key2) -> [root.test.a].key1.key2

            - 基于`根状态`

            >>> get_state(key1, key2, from_="root") -> [root].key1.key2

            - 基于`插件状态`

            >>> get_state(key1, key2, from_="plugin") -> [root.test].key1.key2
        '''
        if from_ == "current":
            keys = [*self.state.keys, *keys]
        elif from_ == "plugin":
            keys = ["root", self.name, *keys]
        elif from_ == "root":
            keys = ["root", *keys]
        else:
            raise

        state = root_state
        for key in keys[1:]:
            state = state[key]
        return state

    def back(self):
        if not self.state.parent:
            return
        self.state.exit()
        # 必须是self.group.state
        self.group.state = self.state.parent
        return self.state

    def goto(self, state: AyakaState = None):
        keys = state.keys

        # 找到第一个不同的结点
        n0 = len(keys)
        n1 = len(self.state.keys)
        n = min(n0, n1)
        for i in range(n):
            if keys[i] != self.state.keys[i]:
                break
        else:
            i += 1

        # 回退
        for j in range(i, n1):
            self.back()
        keys = keys[i:]

        # 重新出发
        # 必须是self.group.state
        state = self.state
        for key in keys:
            state = state[key]
            state.enter()
        self.group.state = state
        return state

    def _get_funcs(self, state: AyakaState, deep: int = 0):
        total_funcs = []

        # 根据深度筛选funcs
        funcs = [
            f for f in state.msg_funcs
            if f.deep == "any" or f.deep >= deep
        ]
        total_funcs.append(funcs)

        # 获取父状态的方法
        if state.parent:
            funcs = self._get_funcs(state.parent, deep+1)
            total_funcs.append(funcs)

        return total_funcs

    def deal(self, msg: Message):
        total_funcs = self._get_funcs(self.state, 0)

        # 测试命令
        for funcs in total_funcs:
            pass

        # 测试消息
        for funcs in total_funcs:
            pass

    def on_state(self, *states: Union[AyakaState, str, List[str]]):
        states = [self._ensure_state(s) for s in states]

        def decorator(func):
            cmds: List[str] = getattr(func, "cmds", None)
            if cmds is not None:
                for s in states:
                    s.on_cmd(cmds, func.deep)
            else:
                func.states = states
            return func
        return decorator

    def on_cmd(self, cmds: List[str], deep: Union[int, Literal["any"]] = 0):
        def decorator(func):
            states: List[AyakaState] = getattr(func, "states", None)
            if states is not None:
                for s in states:
                    s.on_cmd(cmds, deep)
            else:
                func.cmds = cmds
                func.deep = deep
            return func
        return decorator


app = AyakaApp("测试")
s0 = app.get_state("test")
s1 = app.get_state("ok", from_="root")
print(s0, s1)

print(app.state)
app.state = ["test", "ok"]
print(app.state)
app.state = s0
print(app.state)

print(root_state.dict())
