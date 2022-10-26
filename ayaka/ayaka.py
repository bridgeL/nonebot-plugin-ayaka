from importlib import import_module
import json
import asyncio
import datetime
from math import ceil
from pathlib import Path
from collections import defaultdict
from contextvars import ContextVar
from contextlib import asynccontextmanager
from typing import List, Dict, Union, AsyncIterator
from playwright.async_api import async_playwright, Browser, Page, Playwright
from nonebot import logger, get_driver, on_message
from nonebot.adapters.onebot.v11 import Message, MessageSegment, Bot, MessageEvent, GroupMessageEvent


_browser: Browser = None
_playwright: Playwright = None

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

INIT_STATE = "init"

_timer_started = False

# 监听私聊
private_listener_dict: Dict[int, List[int]] = defaultdict(list)

driver = get_driver()

# 配置
# 命令抬头
prefix = getattr(driver.config, "ayaka_prefix", None)
if prefix is None:
    ps = list(driver.config.command_start)
    prefix = ps[0] if len(ps) else "#"
# 参数分割符
sep = getattr(driver.config, "ayaka_separate", None)
if sep is None:
    ss = list(driver.config.command_sep)
    sep = ss[0] if len(ss) else " "
# 是否排除go-cqhttp缓存的过期消息
exclude_old = getattr(driver.config, "ayaka_exclude_old", True)


class AyakaCache:
    def __getattr__(self, name: str):
        return self.__dict__.get(name)


class AyakaApp:
    def __init__(self, name: str) -> None:
        self.name = name
        self.super_triggers: List[AyakaTrigger] = []
        self.state_triggers: List[AyakaTrigger] = []
        self.no_state_triggers: List[AyakaTrigger] = []
        self.timers: List[AyakaTimer] = []
        self._help: Dict[str, str] = {}
        app_list.append(self)

    @property
    def intro(self):
        '''获取介绍，也就是init状态下的帮助'''
        return self._help.get(INIT_STATE, "没有找到帮助")

    @property
    def help(self):
        '''获取当前状态下的帮助，没有找到则返回介绍'''
        if self.group.running_app_name == self.name:
            info = self._help.get(self.group.state)
            if info:
                return info
        return self.intro

    @property
    def all_help(self):
        '''获取介绍以及全部状态下的帮助'''
        info = self.intro
        for k, v in self._help.items():
            if k != INIT_STATE:
                info += f"\n[{k}] {v}"
        return info

    @help.setter
    def help(self, help):
        '''设置帮助，若help为str，则设置为介绍，若help为dict，则设置为对应状态的帮助'''
        if isinstance(help, dict):
            help = {k: v.strip() for k, v in help.items()}
            self._help.update(help)
        else:
            self._help[INIT_STATE] = help.strip()

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

    def plugin_storage(self, *names, default=None):
        '''以app_name划分的独立存储空间，可以实现跨bot、跨群聊的数据共享'''
        names = [str(n) for n in names]
        return AyakaStorage(
            "plugins",
            self.name,
            *names,
            default=default
        )

    def group_storage(self, *names, default=None):
        '''*timer触发时不可用*

        以bot_id、group_id、app_name三级划分分割的独立存储空间'''
        names = [str(n) for n in names]
        return AyakaStorage(
            "groups",
            str(self.bot_id),
            str(self.group_id),
            self.name,
            *names,
            default=default
        )

    async def start(self):
        '''*timer触发时不可用*

        启动应用，并发送提示'''
        f = self.group.set_running_app(self.name)
        if f:
            await self.send(f"已打开应用 [{self.name}]")
        else:
            await self.send("打开应用失败")
        return f

    async def close(self):
        '''*timer触发时不可用*

        关闭应用，并发送提示'''
        f = self.group.set_running_app("")
        if f:
            await self.send(f"已关闭应用 [{self.name}]")
        else:
            await self.send("关闭应用失败")
        return f

    @property
    def state(self):
        '''*timer触发时不可用*

        应用|群组当前状态'''
        if self.name == self.group.running_app_name:
            return self.group.state
        return "未运行"

    def set_state(self, state: str = INIT_STATE):
        '''*timer触发时不可用*

        设置应用|群组当前状态'''
        return self.group.set_state(self.name, state)

    def on_command(self, cmds: Union[List[str], str], super=False):
        '''注册闲置的命令'''
        cmds = ensure_list(cmds)

        if super:
            def decorator(func):
                for cmd in cmds:
                    t = AyakaTrigger(self.name, cmd, None, func)
                    self.super_triggers.append(t)
                return func
            return decorator

        def decorator(func):
            for cmd in cmds:
                t = AyakaTrigger(self.name, cmd, None, func)
                self.no_state_triggers.append(t)
            return func
        return decorator

    def on_state_command(self, cmds: Union[List[str], str], states: Union[List[str], str] = INIT_STATE):
        '''注册应用运行时不同状态下的命令'''
        cmds = ensure_list(cmds)
        states = ensure_list(states)

        def decorator(func):
            for cmd in cmds:
                for state in states:
                    t = AyakaTrigger(self.name, cmd, state, func)
                    self.state_triggers.append(t)
            return func
        return decorator

    def on_text(self, super=False):
        '''注册闲置的消息'''
        return self.on_command("", super=super)

    def on_state_text(self, states: Union[List[str], str] = INIT_STATE):
        '''注册应用运行时不同状态下的消息'''
        return self.on_state_command("", states)

    def on_everyday(self, h: int, m: int, s: int):
        '''每日定时触发'''
        return self.on_interval(86400, h, m, s)

    def on_interval(self, gap: int, h: int = -1, m: int = -1, s: int = -1):
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


class AyakaGroup:
    def __init__(self, bot_id: int, group_id: int) -> None:
        self.bot_id = bot_id
        self.group_id = group_id
        self.running_app_name = ""
        self.state = ""

        self.store_forbid = AyakaStorage(
            "groups",
            str(self.bot_id),
            str(self.group_id),
            "forbid.json",
            default=[]
        )
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

    def get_running_app(self):
        name = self.running_app_name
        if name:
            return self.get_app(name)

    def set_running_app(self, name: str):
        if not name:
            self.running_app_name = ""
            self.state = ""
            return True

        if not self.running_app_name:
            app = self.get_app(name)
            if app:
                self.running_app_name = name
                self.state = INIT_STATE
                return True

    def get_app(self, name: str):
        '''根据app名获取该group所启用的app，不存在则返回None'''
        for app in self.apps:
            if app.name == name:
                return app

    def set_state(self, name: str, state: str):
        '''设置该group的状态'''
        if self.running_app_name == name:
            self.state = state
            return True

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
        if app:
            # 禁用正在运行的应用
            if self.running_app_name == app.name:
                self.running_app_name = ""
                self.state = ""
            # 移除
            self.apps.remove(app)
            # 添加到forbit列表
            app_names: list = self.store_forbid.load()
            if name not in app_names:
                app_names.append(name)
                self.store_forbid.save(app_names)
            return True


class AyakaStorage:
    '''保存为json文件'''

    def __init__(self, *names: str, default=None) -> None:
        self.path = Path("data", *names)

        if not self.path.parent.exists():
            self.path.parent.mkdir(parents=True)

        self.suffix = self.path.suffix

        if not self.path.exists():
            # 这是一个目录
            if not self.suffix:
                self.path.mkdir()

            # 这是一个文件
            # 如果有default就新建并写入内容
            elif default is not None:
                self.save(default)

    @property
    def is_json(self):
        return self.suffix == ".json"

    def load(self):
        if not self.path.exists():
            return None

        with self.path.open("r", encoding="utf8") as f:
            if self.is_json:
                data = json.load(f)
            else:
                data = f.read()
        return data

    def save(self, data):
        with self.path.open("w+", encoding="utf8") as f:
            if self.is_json:
                json.dump(data, f, ensure_ascii=False)
            else:
                f.write(str(data))


class AyakaTrigger:
    def __init__(self, app_name, cmd, state, func) -> None:
        self.app_name = app_name
        self.cmd = cmd
        self.state = state
        self.func = func

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
        logger.opt(colors=True).success(info)

        # 运行回调
        await self.func()


class AyakaTimer:
    def __init__(self, name: str, gap: int, h: int, m: int, s: int, func) -> None:
        self.name = name
        self.h = h
        self.m = m
        self.s = s
        self.gap = gap
        self.func = func

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
            logger.opt(colors=True).success(f"触发定时任务 <y>{self.name}</y>")
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
            return group
    else:
        return AyakaGroup(bot_id, group_id)


def ensure_list(items):
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
    cmd, arg, args = divide_message(message)
    _cmd.set(cmd)
    _arg.set(arg)
    _args.set(args)

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
    app = group.get_running_app()
    if app:
        for t in app.state_triggers:
            if t.state == group.state or t.state == "*":
                triggers.append(t)

    # 其他桌面应用
    else:
        for app in group.apps:
            for t in app.no_state_triggers:
                triggers.append(t)

    await deal_triggers(triggers)


async def deal_triggers(triggers: List[AyakaTrigger]):
    cmd = _cmd.get()

    # 命令
    if cmd:
        for t in triggers:
            if t.cmd == cmd:
                await t.run()
                return True

    # 命令退化成消息
    for t in triggers:
        if not t.cmd:
            await t.run()


def divide_message(message: Message):
    cmd = ""
    arg = message
    args: List[MessageSegment] = []

    for m in message:
        if m.is_text():
            ss = str(m).split(sep)
            args.extend(MessageSegment.text(s) for s in ss if s)
        else:
            args.append(m)

    m = args[0]
    if m.is_text():
        m_str = str(m)
        if m_str.startswith(prefix):
            cmd = m_str[len(prefix):]

            left = str(message[0])[len(m_str):]
            if left.startswith(sep):
                left = left[len(sep):]
            if left:
                left = MessageSegment.text(left)
                arg = Message([left, *message[1:]])
            else:
                arg = Message(message[1:])
            args.pop(0)

    return cmd, arg, args


def load_plugins(path: Path, base=""):
    '''导入指定路径内的全部插件，如果是外部路径，还需要指明前置base'''
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
            logger.opt(colors=True).success(f"{base}<y>{name}</y> 导入成功")


@asynccontextmanager
async def get_new_page(size=None, **kwargs) -> AsyncIterator[Page]:
    ''' 获取playwright Page对象，size接受二元数组输入，设置屏幕大小 size = [宽,高]

        使用示例：
        ```
        async with get_new_page(size=[200,100]) as p:
            await p.goto(...)
            await p.screenshot(...)
        ```
    '''
    if size:
        kwargs["viewport"] = {"width": size[0], "height": size[1]}
    page = await _browser.new_page(**kwargs)
    try:
        yield page
    finally:
        await page.close()


@driver.on_startup
async def startup():
    app_list.sort(key=lambda x: x.name)

    global _browser, _playwright
    _playwright = await async_playwright().start()
    _browser = await _playwright.chromium.launch()


@driver.on_shutdown
async def shutdown():
    if _browser:
        await _browser.close()
    if _playwright:
        await _playwright.stop()


@driver.on_bot_connect
async def bot_connect(bot: Bot):
    bot_list.append(bot)

    global _timer_started
    if not _timer_started:
        _timer_started = True
        for app in app_list:
            for t in app.timers:
                t.start()


@driver.on_bot_disconnect
async def bot_disconnect(bot: Bot):
    bot_list.remove(bot)

on_message(priority=5, block=False, handlers=[deal_event])
