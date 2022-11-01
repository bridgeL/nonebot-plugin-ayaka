from functools import wraps
from importlib import import_module
import asyncio
import datetime
from math import ceil
from pathlib import Path
from collections import defaultdict
from contextvars import ContextVar
from typing import Callable, Coroutine, List, Dict, Union
from nonebot import logger, on_message
from nonebot.adapters.onebot.v11 import Message, MessageSegment, Bot, MessageEvent, GroupMessageEvent

from .storage import AyakaStorage, AyakaStoragePath
from .config import sep, prefix, exclude_old, driver, INIT_STATE, AYAKA_DEBUG
from .playwright import init_chrome, close_chrome


_bot: ContextVar[Bot] = ContextVar("_bot")
_event: ContextVar[MessageEvent] = ContextVar("_event")
_group: ContextVar["AyakaGroup"] = ContextVar("_group")
_arg: ContextVar[Message] = ContextVar("_arg")
_args: ContextVar[List[MessageSegment]] = ContextVar("_args")
_message: ContextVar[Message] = ContextVar("_message")
_cmd: ContextVar[str] = ContextVar("_cmd")
_cache: ContextVar["AyakaCache"] = ContextVar("_cache")

app_list: List["AyakaApp"] = []
group_list: List["AyakaGroup"] = []
bot_list: List[Bot] = []


# 监听私聊
private_listener_dict: Dict[int, List[int]] = defaultdict(list)


class AyakaApp:
    def __repr__(self) -> str:
        return f"AyakaApp({self.name}, {self.state})"

    def __init__(self, name: str) -> None:
        self.name = name
        self.state = INIT_STATE
        self.triggers: List[AyakaTrigger] = []
        self.timers: List[AyakaTimer] = []
        self._help: Dict[str, List[str]] = {}
        self.on = AyakaOn(self)
        self.storage = AyakaStorage(self)
        app_list.append(self)
        if AYAKA_DEBUG:
            print(self)

    @property
    def super_triggers(self):
        return [t for t in self.triggers if t.super]

    @property
    def state_triggers(self):
        return [t for t in self.triggers if not t.super and t.state is not None]

    @property
    def no_state_triggers(self):
        return [t for t in self.triggers if not t.super and t.state is None]

    @property
    def intro(self):
        '''获取介绍，也就是init状态下的帮助'''
        helps = self._help.get(INIT_STATE, ["没有找到帮助"])
        return "\n".join(helps)

    @property
    def help(self):
        '''获取当前状态下的帮助，没有找到则返回介绍'''
        if self.group.running_app_name == self.name:
            helps = self._help.get(self.state, []) + \
                self._help.get("*", [])
            if helps:
                return "\n".join(helps)

        return self.intro

    @property
    def all_help(self):
        '''获取介绍以及全部状态下的帮助'''
        info = self.intro
        for k, v in self._help.items():
            v = "\n".join(v)
            if k != INIT_STATE:
                info += f"\n[{k}]\n{v}"
        return info

    @help.setter
    def help(self, help: Union[str, Dict[str, str]]):
        '''设置帮助，若help为str，则设置为介绍，若help为dict，则设置为对应状态的帮助'''
        if isinstance(help, dict):
            help = {k: [v.strip()] for k, v in help.items()}
            self._help.update(help)
        else:
            self._help[INIT_STATE] = [help.strip()]

    @property
    def valid(self):
        '''*timer触发时不可用*

        当前app是否被当前群组启用
        '''
        return self.group.get_app(self.name)

    @property
    def cache(self):
        '''*timer触发时不可用*

        当前群组、当前app的独立数据空间
        '''
        return _cache.get()

    @property
    def user_name(self):
        '''*timer触发时不可用*

        当前消息的发送人的群名片或昵称
        '''
        s = self.event.sender
        name = s.card or s.nickname
        return name

    @property
    def user_id(self):
        '''*timer触发时不可用*

        当前消息的发送人的uid
        '''
        return self.event.user_id

    @property
    def bot(self):
        '''*timer触发时不可用*

        当前bot
        '''
        return _bot.get()

    @property
    def event(self):
        '''*timer触发时不可用*

        当前消息
        '''
        return _event.get()

    @property
    def group_id(self):
        '''*timer触发时不可用*

        当前群组的id

        注：若群聊A正监听私聊B，当私聊B发送消息触发插件回调时，该属性仍可正确返回群聊A的id
        '''
        return self.group.group_id

    @property
    def bot_id(self):
        '''*timer触发时不可用*

        当前bot的id
        '''
        return self.group.bot_id

    @property
    def group(self):
        '''*timer触发时不可用*

        当前群组

        注：若群聊A正监听私聊B，当私聊B发送消息触发插件回调时，该属性仍可正确返回群聊A
        '''
        return _group.get()

    @property
    def arg(self):
        '''*timer触发时不可用*

        当前消息在移除了命令后的剩余部分
        '''
        return _arg.get()

    @property
    def args(self):
        '''*timer触发时不可用*

        当前消息在移除了命令后，剩余部分按照空格分割后的数组

        注：除了文字消息外，其他消息类型将自动分割，例如一串qq表情会被分割为多个元素
        '''
        return _args.get()

    @property
    def cmd(self):
        '''*timer触发时不可用*

        当前消息的命令头
        '''
        return _cmd.get()

    @property
    def message(self):
        '''*timer触发时不可用*

        当前消息
        '''
        return _message.get()

    async def start(self):
        '''*timer触发时不可用*

        启动应用，并发送提示'''
        name = self.group.running_app_name
        if name and name != self.name:
            await self.send("打开应用失败")
            return False
        self.group.running_app = self
        await self.send(f"已打开应用 [{self.name}]")
        return True

    async def close(self):
        '''*timer触发时不可用*

        关闭应用，并发送提示'''
        name = self.group.running_app_name
        if name:
            self.group.running_app = None
            await self.send(f"已关闭应用 [{name}]")
        else:
            await self.send(f"没有应用在运行")

    def on_handle(self, cmds: Union[List[str], str], states: Union[List[str], str], super: bool):
        '''注册'''
        cmds = ensure_list(cmds)
        states = ensure_list(states)

        def decorator(func: Callable[[], Coroutine]):
            for state in states:
                for cmd in cmds:
                    t = AyakaTrigger(self.name, cmd, state, super, func)
                    self.triggers.append(t)

                # 如果有帮助，自动添加到_help中
                doc = func.__doc__
                if doc:
                    if state is None:
                        state = INIT_STATE
                    if state not in self._help:
                        self._help[state] = []
                    cmd_str = '/'.join(cmds)
                    if not cmd_str:
                        cmd_str = "*"
                    self._help[state].append(f"- {cmd_str} {doc}")

            return func
        return decorator

    def on_timer(self, gap: int, h: int, m: int, s: int):
        '''在指定的时间点后循环触发'''
        def decorator(func):
            t = AyakaTimer(self.name, gap, h, m, s, func)
            self.timers.append(t)
            return func
        return decorator

    def add_listener(self, user_id: int):
        '''为该群组添加对指定私聊的监听'''
        private_listener_dict[user_id].append(self.group_id)

    def remove_listener(self, user_id: int = 0):
        '''默认移除该群组对其他私聊的所有监听'''
        id = self.group_id

        if user_id == 0:
            for ids in private_listener_dict.values():
                if id in ids:
                    ids.remove(id)
            return

        if id in private_listener_dict[user_id]:
            private_listener_dict[user_id].remove(self.group_id)

    async def send(self, message):
        '''发送消息，消息的类型可以是 Message | MessageSegment | str'''
        # 这里不使用event，因为一些event可能来自其他设备的监听传递
        await self.bot.send_group_msg(group_id=self.group_id, message=message)

    async def send_many(self, messages):
        '''发送合并转发消息，消息的类型可以是 List[Message | MessageSegment | str]'''
        length = len(messages)

        # 自动分割长消息组（不可超过100条）谨慎起见，使用80作为单元长度
        div_len = 80
        div_cnt = ceil(length / div_len)
        for i in range(div_cnt):
            # 转换为cqhttp node格式
            msgs = [
                MessageSegment.node_custom(
                    user_id=self.bot_id,
                    nickname="Ayaka Bot",
                    content=str(m)
                )
                for m in messages[i*div_len: (i+1)*div_len]
            ]
            await self.bot.call_api("send_group_forward_msg", group_id=self.group_id, messages=msgs)

    async def t_send(self, bot_id: int, group_id: int, message):
        '''timer触发回调时，想要发送消息必须使用该方法，一些上下文亦无法使用'''
        # 未连接
        bot = get_bot(bot_id)
        if not bot:
            logger.warning(f"{bot_id} 未连接")
            return

        # 已禁用
        group = get_group(bot_id, group_id)
        app = group.get_app(self.name)
        if not app:
            return

        await bot.send_group_msg(group_id=group_id, message=message)


class AyakaCache:
    def __getattr__(self, name: str):
        return self.__dict__.get(name)


class AyakaOn:
    def __init__(self, app: AyakaApp) -> None:
        self.app = app
        self.chain_dict: Dict[str, int] = {}

    def everyday(self, h: int, m: int, s: int):
        '''每日定时触发'''
        return self.interval(86400, h, m, s)

    def interval(self, gap: int, h=-1, m=-1, s=-1):
        '''在指定的时间点后循环触发'''
        return self.app.on_timer(gap, h, m, s)

    def state(self, states: Union[List[str], str] = INIT_STATE):
        '''注册有状态回调'''
        def decorator(func):
            # 取出之前存的参数
            return self.app.on_handle(func.cmds, states, False)(func)
        return decorator

    def idle(self, super=False):
        '''注册无状态回调'''
        def decorator(func):
            # 取出之前存的参数
            return self.app.on_handle(func.cmds, None, super)(func)
        return decorator

    def chain(self, name: str):
        '''注册状态链条'''
        def decorator(func):
            # 取出之前存的参数
            chain_type = func.chain_type
            cmds = func.cmds

            # 状态转移链起始
            if chain_type == "begin":
                from_states = func.from_states
                next_state = self._get_chain_state(name)
                return self._create_decorator(cmds, from_states, next_state)(func)

            # 状态转移链+1
            elif chain_type == "next":
                last_state = self._get_chain_state(name)
                self._add_chain_state(name)
                next_state = self._get_chain_state(name)
                return self._create_decorator(cmds, last_state, next_state)(func)

            # 状态转移链结束
            else:
                last_state = self._get_chain_state(name)
                to_state = func.to_state
                return self._create_decorator(cmds, last_state, to_state)(func)
        return decorator

    def command(self, *cmds: str):
        def decorator(func):
            func.cmds = cmds
            return func
        return decorator

    def text(self):
        def decorator(func):
            func.cmds = ""
            return func
        return decorator

    def begin(self, from_states: Union[List[str], str, None] = INIT_STATE):
        def decorator(func):
            func.from_states = from_states
            func.chain_type = "begin"
            return func
        return decorator

    def next(self):
        def decorator(func):
            func.chain_type = "next"
            return func
        return decorator

    def end(self, to_state: Union[str, None] = INIT_STATE):
        def decorator(func):
            func.to_state = to_state
            func.chain_type = "end"
            return func
        return decorator

    def _get_chain_state(self, name):
        if name not in self.chain_dict:
            self.chain_dict[name] = 0
        return f"{name}_{self.chain_dict[name]}"

    def _add_chain_state(self, name):
        self.chain_dict[name] += 1

    def _create_decorator(self, cmds, last_states, next_state):
        # 生成state chain专用的装饰器
        # 执行回调前后，应用状态从last_states 转移到 next_state
        def decorator(func):
            # 为原方法添加设置状态转移的代码
            if last_states is None:
                @wraps(func)
                async def _func():
                    if not await self.app.start():
                        return
                    await func()
                    self.app.state = next_state

            elif next_state is None:
                @wraps(func)
                async def _func():
                    code = await func()
                    # 原方法返回任意负数，视为中断该状态转移链
                    if isinstance(code, int) and code < 0:
                        return
                    await self.app.close()

            else:
                @wraps(func)
                async def _func():
                    code = await func()
                    # 原方法返回任意负数，视为中断该状态转移链
                    if isinstance(code, int) and code < 0:
                        return
                    self.app.state = next_state

            # 注册回调
            self.app.on_handle(cmds, last_states, False)(_func)
        return decorator


class AyakaGroup:
    def __repr__(self) -> str:
        return f"AyakaGroup({self.bot_id}, {self.group_id}, {self.apps})"

    def __init__(self, bot_id: int, group_id: int) -> None:
        self.bot_id = bot_id
        self.group_id = group_id
        self.running_app: AyakaApp = None

        self.store_forbid = AyakaStoragePath(
            "groups",
            self.bot_id,
            self.group_id
        ).jsonfile("forbid", [])

        # 读取forbit列表
        forbid_names = self.store_forbid.load()

        # 添加app，并分配独立数据空间
        self.apps: List["AyakaApp"] = []
        self.cache_dict = {}
        for app in app_list:
            if app.name not in forbid_names:
                self.apps.append(app)
                self.cache_dict[app.name] = AyakaCache()

        group_list.append(self)

        if AYAKA_DEBUG:
            print(self)

    @property
    def running_app_name(self):
        if self.running_app:
            return self.running_app.name
        return ""

    def get_app(self, name: str):
        '''根据app名获取该group所启用的app，不存在则返回None'''
        for app in self.apps:
            if app.name == name:
                return app

    def permit_app(self, name: str):
        '''启用指定app'''
        if self.get_app(name):
            return True

        for app in app_list:
            if app.name == name:
                self.apps.append(app)
                # 从forbit列表移除
                app_names: list = self.store_forbid.load()
                if name in app_names:
                    app_names.remove(name)
                    self.store_forbid.save(app_names)
                return True

    def forbid_app(self, name: str):
        '''禁用指定app'''
        if name == "ayaka_master":
            return

        app = self.get_app(name)
        if not app:
            return

        # 禁用正在运行的应用
        if self.running_app_name == name:
            self.running_app = None

        # 移除
        self.apps.remove(app)

        # 添加到forbit列表
        app_names: list = self.store_forbid.load()
        if name not in app_names:
            app_names.append(name)
            self.store_forbid.save(app_names)
        return True


class AyakaTrigger:
    def __repr__(self) -> str:
        return f"AyakaTrigger({self.app_name}, {self.cmd}, {self.state}, {self.super}, {self.func.__name__})"

    def __init__(self, app_name, cmd, state, super, func) -> None:
        self.app_name = app_name
        self.cmd = cmd
        self.state = state
        self.super = super
        self.func = func
        if AYAKA_DEBUG:
            print(self)

    async def run(self):
        # 切换到对应数据空间
        group = _group.get()
        cache = group.cache_dict.get(self.app_name)
        _cache.set(cache)

        # 日志记录
        info = f"已触发应用 "
        if self.state is not None:
            info += f"<y>{self.app_name}</y>|<g>{self.state}</g> "
        else:
            info += f"<y>{self.app_name}</y> "
        if self.cmd:
            info += f"命令 <y>{self.cmd}</y> "
        else:
            info += "消息 "
        info += f"执行回调 <c>{self.func.__name__}</c>"
        logger.opt(colors=True).debug(info)

        # 运行回调
        await self.func()


class AyakaTimer:
    def __repr__(self) -> str:
        return f"AyakaTimer({self.name}, {self.gap}, {self.func.__name__})"

    def __init__(self, name: str, gap: int, h: int, m: int, s: int, func) -> None:
        self.name = name
        self.h = h
        self.m = m
        self.s = s
        self.gap = gap
        self.func = func
        if AYAKA_DEBUG:
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
            logger.opt(colors=True).debug(f"触发定时任务 <y>{self.name}</y>")
            asyncio.create_task(self.func())
            await asyncio.sleep(self.gap)


def get_bot(bot_id: int):
    '''获取已连接的bot'''
    bot_id = str(bot_id)
    for bot in bot_list:
        if bot.self_id == bot_id:
            return bot


def get_group(bot_id: int, group_id: int):
    '''获取对应的AyakaGroup对象，自动增加'''
    for group in group_list:
        if group.bot_id == bot_id and group.group_id == group_id:
            break
    else:
        group = AyakaGroup(bot_id, group_id)
    return group


def ensure_list(items):
    if isinstance(items, tuple):
        return [item for item in items]
    if not isinstance(items, list):
        return [items]
    return items


async def deal_event(bot: Bot, event: MessageEvent):
    if exclude_old:
        time_i = int(datetime.datetime.now().timestamp())
        if event.time < time_i - 60:
            return

    _bot.set(bot)
    _event.set(event)

    bot_id = int(bot.self_id)

    if isinstance(event, GroupMessageEvent):
        group_id = event.group_id
        await deal_group(bot_id, group_id)

    else:
        id = event.user_id
        group_ids = private_listener_dict.get(id, [])
        ts = [asyncio.create_task(deal_group(bot_id, group_id))
              for group_id in group_ids]
        await asyncio.gather(*ts)


async def deal_group(bot_id: int, group_id: int):
    # 群组
    group = get_group(bot_id, group_id)
    _group.set(group)

    # 消息
    message = _event.get().message
    _message.set(message)

    # 命令、参数
    cmd = get_cmd(message)
    _cmd.set(cmd)

    # 让super先来
    triggers = []
    for app in group.apps:
        for t in app.super_triggers:
            triggers.append(t)

    # 若执行了super命令，则退出
    if await deal_triggers(triggers):
        return

    # 普通命令继续
    triggers = []

    # 当前正在运行
    app = group.running_app
    if app:
        for t in app.state_triggers:
            if t.state == app.state or t.state == "*":
                triggers.append(t)

    # 其他桌面应用
    else:
        for app in group.apps:
            for t in app.no_state_triggers:
                triggers.append(t)

    await deal_triggers(triggers)


async def deal_triggers(triggers: List[AyakaTrigger]):
    cmd = _cmd.get()
    msg = _message.get()

    # 命令
    if cmd:
        for t in triggers:
            if t.cmd == cmd:
                # 设置去掉命令后的消息
                arg = remove_cmd(cmd, msg)
                _arg.set(arg)
                _args.set(divide_message(arg))
                await t.run()
                return True

    _arg.set(msg)
    _args.set(divide_message(msg))

    # 命令退化成消息
    for t in triggers:
        if not t.cmd:
            await t.run()


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
        m_str = m_str[len(prefix+cmd):]
        if not m_str:
            message.pop(0)
        else:
            message[0] = MessageSegment.text(m_str)
    return message


def load_plugins(path: Path, base=""):
    '''导入指定路径内的全部插件，如果是外部路径，还需要指明前置base

    不推荐使用，此API不明确且已落时'''
    if not path.is_dir():
        logger.error(f"{path} 不是路径")
        return

    if not base:
        base = ".".join(path.relative_to(Path.cwd()).parts)
    if base:
        base += "."

    for p in path.iterdir():
        name = p.stem
        if name.startswith("_") or name.startswith("."):
            continue

        module_name = base + name
        try:
            import_module(module_name)
        except:
            logger.opt(colors=True).exception(f"{base}<y>{name}</y> 导入失败")
        else:
            logger.opt(colors=True).debug(f"{base}<y>{name}</y> 导入成功")


@driver.on_startup
async def startup():
    app_list.sort(key=lambda x: x.name)
    await init_chrome()

    # 在一切准备就绪后，开启插件中的定时模块
    for app in app_list:
        for t in app.timers:
            t.start()


@driver.on_shutdown
async def shutdown():
    await close_chrome()


@driver.on_bot_connect
async def bot_connect(bot: Bot):
    bot_list.append(bot)


@driver.on_bot_disconnect
async def bot_disconnect(bot: Bot):
    bot_list.remove(bot)

on_message(priority=5, block=False, handlers=[deal_event])
