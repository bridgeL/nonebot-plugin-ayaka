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
from nonebot.adapters.onebot.v11 import Message, MessageSegment, Bot, MessageEvent, GroupMessageEvent, escape
from nonebot.adapters.onebot.v11.exception import ActionFailed, NetworkError, OneBotV11AdapterException


_browser: Browser = None
_playwright: Playwright = None

_bot: ContextVar[Bot] = ContextVar("_bot")
_event: ContextVar[MessageEvent] = ContextVar("_event")
_group: ContextVar["AyakaGroup"] = ContextVar("_group")
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
try:
    prefix = list(driver.config.command_start)[0]
except:
    prefix = "#"
# 参数分割符
try:
    sep = list(driver.config.command_sep)[0]
except:
    sep = " "
# 是否排除go-cqhttp缓存的过期消息
try:
    exclude_old = driver.config.ayaka_exclude_old
except:
    exclude_old = True


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
        return self._help.get(INIT_STATE, "没有找到帮助")

    @property
    def help(self):
        if self.group.running_app_name == self.name:
            info = self._help.get(self.group.state)
            if info:
                return info
        return self.intro

    @property
    def all_help(self):
        info = self.intro
        for k, v in self._help.items():
            if k != INIT_STATE:
                info += f"\n[{k}] {v}"
        return info

    @help.setter
    def help(self, help):
        if isinstance(help, dict):
            self._help.update(help)
        else:
            self._help[INIT_STATE] = help

    @property
    def valid(self):
        return self.group.get_app(self.name)

    @property
    def cache(self):
        return _cache.get()

    @property
    def user_name(self):
        s = self.event.sender
        name = s.card or s.nickname
        return name

    @property
    def user_id(self):
        return self.event.user_id

    @property
    def bot(self):
        return _bot.get()

    @property
    def event(self):
        return _event.get()

    @property
    def group_id(self):
        return self.group.group_id

    @property
    def bot_id(self):
        return self.group.bot_id

    @property
    def group(self):
        return _group.get()

    @property
    def args(self):
        return _args.get()

    @property
    def cmd(self):
        return _cmd.get()

    @property
    def message(self):
        return _message.get()

    def plugin_storage(self, *names, suffix=".json", default=None):
        '''以app_name划分的独立存储空间，可以实现跨bot、跨群聊的数据共享'''
        return AyakaStorage(
            "plugins",
            self.name,
            *names,
            suffix=suffix,
            default=default
        )

    def group_storage(self, *names, suffix=".json", default=None):
        '''以bot_id、group_id、app_name三级划分分割的独立存储空间'''
        return AyakaStorage(
            "groups",
            self.bot_id,
            self.group_id,
            self.name,
            *names,
            suffix=suffix,
            default=default
        )

    async def start(self):
        f = self.group.set_running_app(self.name)
        if f:
            await self.send(f"已打开应用 [{self.name}]")
        else:
            await self.send("打开应用失败")
        return f

    async def close(self):
        f = self.group.set_running_app("")
        if f:
            await self.send(f"已关闭应用 [{self.name}]")
        else:
            await self.send("关闭应用失败")
        return f

    @property
    def state(self):
        if self.name == self.group.running_app_name:
            return self.group.state
        return "未运行"

    def set_state(self, state: str = INIT_STATE):
        return self.group.set_state(self.name, state)

    def on_command(self, cmds: Union[List[str], str], super=False):
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
        return self.on_command("", super=super)

    def on_state_text(self, states: Union[List[str], str] = INIT_STATE):
        return self.on_state_command("", states)

    def on_everyday(self, h: int, m: int, s: int):
        return self.on_interval(86400, h, m, s)

    def on_interval(self, gap: int, h: int = -1, m: int = -1, s: int = -1):
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
        # 这里不使用event，因为一些event可能来自其他设备的监听传递
        await self.bot.send_group_msg(group_id=self.group_id, message=message)

    async def send_many(self, messages):
        length = len(messages)

        # 自动分割长消息组（不可超过100条）谨慎起见，使用80作为单元长度
        div_len = 80
        div_cnt = ceil(length / div_len)
        for i in range(div_cnt):
            msgs = messages[i*div_len: (i+1)*div_len]
            # 转换为cqhttp node格式
            nodes = self.pack_message_nodes(msgs)
            await self.bot.call_api("send_group_forward_msg", group_id=self.group_id, messages=nodes)

    async def t_send(self, bot_id: int, group_id: int, message):
        '''timer触发回调时，想要发送消息必须使用该方法，一些上下文亦无法使用'''
        # 未连接
        bot = get_bot(bot_id)
        if not bot:
            logger.warning(f"{bot_id} 未连接")
            return

        # 已禁用
        if not check_app_permit(bot_id, group_id, self.name):
            return

        await bot.send_group_msg(group_id=group_id, message=message)

    def pack_message_nodes(self, items: list):
        '''
            将数组打包为message_node格式的数组
        '''
        nodes = []
        for m in items:
            nodes.append({
                "type": "node",
                "data": {
                    "name": "Ayaka Bot",
                    "uin": self.bot.self_id,
                    "content": escape(str(m), escape_comma=False)
                }
            })
        return nodes


class AyakaGroup:
    def __init__(self, bot_id: int, group_id: int) -> None:
        self.bot_id = bot_id
        self.group_id = group_id
        self.running_app_name = ""
        self.state = None
        self.store_forbid = AyakaStorage(
            "groups",
            self.bot_id,
            self.group_id,
            "forbid",
            default=[]
        )
        # 读取forbit列表
        forbid_names = self.store_forbid.load()
        self.apps: List["AyakaApp"] = []
        self.cache_dict = {}
        for app in app_list:
            if app.name not in forbid_names:
                self.apps.append(app)
                self.cache_dict[app.name] = AyakaCache()
        group_list.append(self)

    def set_cache(self, name: str):
        cache = self.cache_dict.get(name)
        if cache:
            _cache.set(cache)

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
        for app in self.apps:
            if app.name == name:
                return app

    def set_state(self, name: str, state: str):
        if self.running_app_name == name:
            self.state = state
            return True

    def permit_app(self, name: str):
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
        if name == "_master":
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

    def __init__(self, *names, suffix=".json", default=None) -> None:
        names = [str(n) for n in names]
        self.path = Path("data", *names)
        if suffix:
            self.path = self.path.with_suffix(suffix)

        if not self.path.parent.exists():
            self.path.parent.mkdir(parents=True)

        if suffix and default is not None and not self.path.exists():
            self.save(default)

    def load(self):
        if not self.path.exists():
            return None

        with self.path.open("r", encoding="utf8") as f:
            data = json.load(f)
        return data

    def save(self, data):
        with self.path.open("w+", encoding="utf8") as f:
            json.dump(data, f, ensure_ascii=False)


class AyakaTrigger:
    def __init__(self, app_name, cmd, state, func) -> None:
        self.app_name = app_name
        self.cmd = cmd
        self.state = state
        self.func = func

    async def run(self):
        _group.get().set_cache(self.app_name)
        info = f"已触发应用 <y>{self.app_name}</y> "
        if self.state is not None:
            info += f"[\"<g>{self.state}</g>\"] "
        if self.cmd:
            info += f"命令 <y>{self.cmd}</y> "
        else:
            info += "消息 "
        info += f"执行回调 <c>{self.func.__name__}</c>"
        logger.opt(colors=True).success(info)
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
    bot_id = str(bot_id)
    for bot in bot_list:
        if bot.self_id == bot_id:
            return bot


def get_group(bot_id: int, group_id: int):
    '''自动增加'''
    for group in group_list:
        if group.bot_id == bot_id and group.group_id == group_id:
            return group
    else:
        return AyakaGroup(bot_id, group_id)


def check_app_permit(bot_id: int, group_id: int, name: str):
    group = get_group(bot_id, group_id)
    app = group.get_app(name)
    return app is not None


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
    group = get_group(bot_id, group_id)
    _group.set(group)

    # 消息
    message = _event.get().message
    _message.set(message)

    # 命令、参数
    cmd, args = divide_message(message)
    _cmd.set(cmd)
    _args.set(args)

    # 让super先来
    triggers = []
    for app in group.apps:
        for t in app.super_triggers:
            triggers.append(t)

    await deal_triggers(triggers)

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
                return

    # 命令退化成消息
    for t in triggers:
        if not t.cmd:
            await t.run()


def divide_message(message: Message):
    args: List[MessageSegment] = []
    for m in message:
        if m.is_text():
            ss = str(m).split(sep)
            args.extend(MessageSegment.text(s) for s in ss)
        else:
            args.append(m)

    cmd = ""

    m = args[0]
    if m.is_text():
        m_str = str(m)
        if m_str.startswith(prefix):
            cmd = m_str[1:]
            args.pop(0)

    return cmd, args


@asynccontextmanager
async def get_new_page(size=None, **kwargs) -> AsyncIterator[Page]:
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
