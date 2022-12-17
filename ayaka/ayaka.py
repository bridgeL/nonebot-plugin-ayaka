'''ayaka核心'''
import asyncio
import datetime
import inspect
import json
from math import ceil
from pathlib import Path
import re
from loguru import logger
from typing import List, Dict, Literal, Tuple, Union
from .depend import AyakaCache
from .config import ayaka_root_config, ayaka_data_path
from .constant import _bot, _event, _group, _arg, _args, _message, _cmd, _cmd_regex, _enter_exit_during, app_list, group_list, bot_list, private_listener_dict
from .driver import on_message, get_driver, Message, MessageSegment, Bot, MessageEvent, GroupMessageEvent
from .state import AyakaState, AyakaTrigger, AyakaTimer, root_state, ensure_regex_list
from .on import AyakaOn


class AyakaGroup:
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.bot_id}, {self.group_id}, {self.apps})"

    def __init__(self, bot_id: int, group_id: int) -> None:
        self.bot_id = bot_id
        self.group_id = group_id
        self.state = root_state

        # 添加app，并分配独立数据空间
        self.apps: List["AyakaApp"] = []
        self.cache_dict: Dict[str, Dict[str, AyakaCache]] = {}
        for app in app_list:
            # if app.name not in forbid_names:
            self.apps.append(app)
            self.cache_dict[app.name] = {}

        group_list.append(self)

        if ayaka_root_config.debug:
            print(self)

    async def enter(self, state: Union[str, List[str], AyakaState]):
        if isinstance(state, list):
            next_state = self.state.join(*state)
        elif isinstance(state, str):
            next_state = self.state.join(state)
        else:
            next_state = self.state.join(*state.keys)
        return await self.goto(next_state)

    async def back(self):
        if self.state.parent:
            await self.state.exit()
            self.state = self.state.parent
            return self.state

    async def goto(self, state: AyakaState):
        if _enter_exit_during.get() > 0:
            logger.warning("你正在AyakaState的enter/exit方法中进行状态转移，这可能会导致无法预料的错误")

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
            await self.back()
        keys = keys[i:]

        # 重新出发
        for key in keys:
            self.state = self.state[key]
            await self.state.enter()
        logger.opt(colors=True).debug(f"状态：<c>{self.state}</c>")
        return self.state

    def get_app(self, name: str):
        '''根据app名获取该group所启用的app，不存在则返回None'''
        for app in self.apps:
            if app.name == name:
                return app


class AyakaApp:
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"

    def __init__(self, name: str) -> None:
        self.path = Path(inspect.stack()[1].filename)
        logger.opt(colors=True).debug(f"加载应用 \"<c>{name}</c>\"")

        for app in app_list:
            if app.name == name:
                raise Exception(
                    f"应用{app.name} 重复注册，已忽略注册时间更晚的应用！\n{app.path}(最早注册)\n{self.path}(被忽略)")

        self.name = name
        self.ayaka_root_config = ayaka_root_config
        self.funcs = []
        self.on = AyakaOn(self)
        self.timers: List[AyakaTimer] = []

        self.root_state = root_state
        self.plugin_state = self.get_state()

        self._intro = "没有介绍"
        self.state_helps: Dict[str, List[str]] = {}
        self.idle_helps: List[str] = []

        app_list.append(self)
        if ayaka_root_config.debug:
            print(self)

    @property
    def intro(self):
        help = self._intro
        for h in self.idle_helps:
            help += "\n" + h
        return help

    @property
    def all_help(self):
        help = self.intro
        for s, hs in self.state_helps.items():
            help += f"\n[{s}]"
            for h in hs:
                help += "\n" + h
        return help

    @property
    def help(self):
        '''获取当前状态下的帮助，没有找到则返回介绍'''
        total_triggers = get_cascade_triggers(self.state)

        helps = []
        cmds = []
        for ts in total_triggers:
            flag = 1
            for t in ts:
                if t.app == self:
                    for c in t.raw_cmds:
                        if c in cmds:
                            break
                    else:
                        if flag:
                            helps.append(f"[{t.state[1:]}]")
                            flag = 0
                        cmds.extend(t.raw_cmds)
                        helps.append(t.help)

        if not helps:
            return self.intro
        return "\n".join(helps)

    @help.setter
    def help(self, help: str):
        self._intro = help

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
    def cache(self):
        '''*timer触发时不可用*

        当前群组的缓存空间'''
        return self.group.cache_dict[self.name]

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
    def cmd_regex(self):
        '''*timer触发时不可用*

        当前消息的命令头
        '''
        return _cmd_regex.get()

    @property
    def message(self):
        '''*timer触发时不可用*

        当前消息
        '''
        return _message.get()

    @property
    def state(self):
        return self.group.state

    def get_state(self, key: Union[str, List[str]] = [], *_keys: str):
        # _keys为兼容旧API（0.5.3及以前
        '''
            假设当前app.name为test

            >>> get_state(key1) -> [root.test].key1

            >>> get_state([key1, key2]) -> [root.test].key1.key2

            特别的，参数可以为空，例如：

            >>> get_state() -> [root.test]
        '''
        if isinstance(key, list):
            _keys = [self.name, *key]
        else:
            _keys = [self.name, key, *_keys]

        keys = []
        for k in _keys:
            keys.extend(k.split(ayaka_root_config.state_separate))

        return root_state.join(*keys)

    async def set_state(self, state: Union[AyakaState, str, List[str]], *keys: str):
        '''变更当前群组的状态，state可以是AyakaState、字符串或字符串列表，若字符串内包含.符号，还会自动对其进行分割'''
        return await self.goto(state, *keys)

    async def goto(self, state: Union[AyakaState, str, List[str]], *keys: str):
        # keys为兼容旧API（0.5.2及以前
        '''变更当前群组的状态，state可以是AyakaState、字符串或字符串列表，若字符串内包含.符号，还会自动对其进行分割'''
        if isinstance(state, str):
            state = self.get_state(state, *keys)
        elif isinstance(state, list):
            state = self.get_state(*state)
        return await self.group.goto(state)

    async def enter(self, state: Union[str, List[str], AyakaState]):
        '''进入子状态'''
        return await self.group.enter(state)

    async def back(self):
        '''回退当前群组的状态'''
        return await self.group.back()

    def _add_func(self, func):
        '''如果不存在就加入self.funcs'''
        if func not in self.funcs:
            self.funcs.append(func)

    def on_deep_all(self, deep: Union[int, Literal["all"]] = "all"):
        '''注册深度监听'''
        def decorator(func):
            func.deep = deep
            self._add_func(func)
            return func
        return decorator

    def on_no_block(self, block: bool = False):
        '''注册非阻断'''
        def decorator(func):
            func.block = block
            self._add_func(func)
            return func
        return decorator

    def on_cmd(self, *cmds: Union[str, re.Pattern]):
        '''注册命令触发，不填写命令则视为文本消息'''
        def decorator(func):
            func.cmds = getattr(func, "cmds", [])
            func.cmds.extend(ensure_regex_list(cmds))
            self._add_func(func)
            return func
        return decorator

    def on_regex(self, *cmds: Union[str, re.Pattern]):
        '''注册命令触发，不填写命令则视为文本消息'''
        def decorator(func):
            func.cmds = getattr(func, "cmds", [])
            func.cmds.extend(ensure_regex_list(cmds, False))
            self._add_func(func)
            return func
        return decorator

    def on_text(self):
        '''注册消息触发'''
        def decorator(func):
            self._add_func(func)
            return func
        return decorator

    def on_state(self, *states: Union[AyakaState, str, List[str]]):
        '''注册有状态响应，不填写states则为plugin_state'''
        _states = []

        if not states:
            _states = [self.plugin_state]

        else:
            for s in states:
                if isinstance(s, str):
                    s = self.get_state(s)
                elif isinstance(s, list):
                    s = self.get_state(*s)
                _states.append(s)

        def decorator(func):
            func.states = _states
            self._add_func(func)
            return func
        return decorator

    def on_idle(self):
        '''注册根结点回调'''
        return self.on_state(self.root_state)

    def on_everyday(self, h: int, m: int, s: int):
        '''每日定时触发'''
        return self.on_interval(86400, h, m, s)

    def on_interval(self, gap: int, h=-1, m=-1, s=-1, show=True):
        '''在指定的时间点后循环触发'''
        def decorator(func):
            t = AyakaTimer(self, gap, h, m, s, func, show)
            self.timers.append(t)
            return func
        return decorator

    def on_start_cmds(self, *cmds: Union[str, re.Pattern]):
        def decorator(func):
            func = self.on_idle()(func)
            func = self.on_cmd(*cmds)(func)
            return func
        return decorator

    def on_close_cmds(self, *cmds: Union[str, re.Pattern]):
        def decorator(func):
            func = self.on_state()(func)
            func = self.on_deep_all()(func)
            func = self.on_cmd(*cmds)(func)
            return func
        return decorator

    def set_start_cmds(self, *cmds: Union[str, re.Pattern]):
        '''设置应用启动命令，当然，你也可以通过app.on_start_cmds自定义启动方式'''
        @self.on_start_cmds(*cmds)
        async def start():
            '''打开应用'''
            await self.start()

    def set_close_cmds(self, *cmds: Union[str, re.Pattern]):
        '''设置应用关闭命令，当然，你也可以通过app.on_close_cmds自定义关闭方式'''
        @self.on_close_cmds(*cmds)
        async def close():
            '''关闭应用'''
            await self.close()

    async def start(self, state: str = ""):
        '''*timer触发时不可用*

        启动应用，并发送提示

        state参数为兼容旧API'''
        if not state:
            state = self.get_state()
        await self.goto(state)
        await self.send(f"已打开应用 [{self.name}]")

    async def close(self):
        '''*timer触发时不可用*

        关闭应用，并发送提示'''
        await self.goto(root_state)
        await self.send(f"已关闭应用 [{self.name}]")

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

    def pack_messages(self, bot_id, messages):
        '''转换为cqhttp node格式'''
        data: List[MessageSegment] = []
        for m in messages:
            if isinstance(m, MessageSegment) and m.type == "node":
                data.append(m)
            else:
                m = MessageSegment.node_custom(
                    user_id=bot_id,
                    nickname="Ayaka Bot",
                    content=str(m)
                )
                data.append(m)
        return data

    async def send_many(self, messages):
        '''发送合并转发消息，消息的类型可以是 List[Message | MessageSegment | str]'''
        # 分割长消息组（不可超过100条
        div_len = 100
        div_cnt = ceil(len(messages) / div_len)
        for i in range(div_cnt):
            msgs = self.pack_messages(
                self.bot_id,
                messages[i*div_len: (i+1)*div_len]
            )
            await self.bot.call_api("send_group_forward_msg", group_id=self.group_id, messages=msgs)

    def t_check(self, bot_id: int):
        # 未连接
        bot = get_bot(bot_id)
        if not bot:
            logger.warning(f"BOT({bot_id}) 未连接")
            return

        return bot

    async def t_send(self, bot_id: int, group_id: int, message):
        '''timer触发回调时，想要发送消息必须使用该方法，一些上下文亦无法使用'''
        bot = self.t_check(bot_id)
        if not bot:
            return

        await bot.send_group_msg(group_id=group_id, message=message)

    async def t_send_many(self, bot_id: int, group_id: int, messages):
        '''timer触发回调时，想要发送消息必须使用该方法，一些上下文亦无法使用'''
        bot = self.t_check(bot_id)
        if not bot:
            return

        # 分割长消息组（不可超过100条）谨慎起见，使用80作为单元长度
        div_len = 80
        div_cnt = ceil(len(messages) / div_len)
        for i in range(div_cnt):
            msgs = self.pack_messages(
                bot_id,
                messages[i*div_len: (i+1)*div_len]
            )
            await bot.call_api("send_group_forward_msg", group_id=group_id, messages=msgs)


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


def get_app(app_name: str):
    for app in app_list:
        if app.name == app_name:
            return app


async def deal_event(bot: Bot, event: MessageEvent):
    '''处理收到的消息，将其分割为cmd和args，设置上下文相关变量的值，并将消息传递给对应的群组'''
    if ayaka_root_config.exclude_old_msg:
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
    prefix = ayaka_root_config.prefix

    # 群组
    group = get_group(bot_id, group_id)
    _group.set(group)

    # 消息
    message = _event.get().message
    _message.set(message)

    # 从子状态开始向上查找可用的触发
    state = group.state
    cascade_triggers = get_cascade_triggers(state, 0)

    # 命令
    # 消息前缀文本
    first = get_first(message)
    if first.startswith(prefix):
        first = first[len(prefix):]
        for ts in cascade_triggers:
            if await deal_cmd_triggers(ts, message, first, state):
                return

    # 命令退化成消息
    for ts in cascade_triggers:
        if await deal_text_triggers(ts, message, state):
            return


async def deal_cmd_triggers(triggers: List[AyakaTrigger], message: Message, first: str, state: AyakaState):
    sep = ayaka_root_config.separate

    # 找到触发命令
    cmd_ts: List[Tuple[re.Pattern, str, AyakaTrigger]] = []
    for t in triggers:
        for cmd in t.cmds:
            r = cmd.match(first)
            if r:
                cmd_ts.append([r, r.group(), t])
                break

    # 根据命令长度排序，长命令优先级更高
    cmd_ts.sort(key=lambda x: len(x[1]), reverse=1)

    for r, c, t in cmd_ts:
        # 设置上下文
        # 设置命令
        _cmd.set(c)
        _cmd_regex.set(r)
        # 设置参数
        left = first[len(c):].lstrip(sep)
        if left:
            arg = Message([MessageSegment.text(left), *message[1:]])
        else:
            arg = Message(message[1:])
        _arg.set(arg)
        _args.set(divide_message(arg))

        # 记录触发
        log_trigger(c, t.app.name, state, t.func.__name__)
        f = await t.run()

        # 阻断后续
        if f and t.block:
            return True


async def deal_text_triggers(triggers: List[AyakaTrigger], message: Message, state: AyakaState):
    # 消息
    text_ts = [t for t in triggers if not t.cmds]

    # 设置上下文
    # 设置参数
    _arg.set(message)
    _args.set(divide_message(message))

    for t in text_ts:
        # 记录触发
        log_trigger("", t.app.name, state, t.func.__name__)
        f = await t.run()

        # 阻断后续
        if f and t.block:
            return True


def get_cascade_triggers(state: AyakaState, deep: int = 0):
    # 根据深度筛选funcs
    ts = [
        t for t in state.triggers
        if t.deep == "all" or t.deep >= deep
    ]
    cascade_triggers = [ts]

    # 获取父状态的方法
    if state.parent:
        cascade_triggers.extend(get_cascade_triggers(state.parent, deep+1))

    # 排除空项
    cascade_triggers = [ts for ts in cascade_triggers if ts]
    return cascade_triggers


def log_trigger(cmd, app_name, state, func_name):
    '''日志记录'''
    items = []
    items.append(f"状态：<c>{state}</c>")
    items.append(f"应用：<y>{app_name}</y>")
    if cmd:
        items.append(f"命令：<y>{cmd}</y>")
    else:
        items.append("命令：<g>无</g>")
    items.append(f"回调：<c>{func_name}</c>")
    info = " | ".join(items)
    logger.opt(colors=True).debug(info)


def get_first(message: Message):
    first = ""
    for m in message:
        if m.type == "text":
            first += str(m)
        else:
            break
    return first


def divide_message(message: Message) -> List[MessageSegment]:
    args = []
    sep = ayaka_root_config.separate

    for m in message:
        if m.is_text():
            ss = str(m).split(sep)
            args.extend(MessageSegment.text(s) for s in ss if s)
        else:
            args.append(m)

    return args


def regist_func(app: AyakaApp, func):
    '''注册回调'''
    # 默认是无状态应用，从root开始触发
    states: List[AyakaState] = getattr(func, "states", [root_state])
    # 默认是消息响应
    cmds: List[re.Pattern] = getattr(func, "cmds", [])
    # 默认监听深度为0
    deep: int = getattr(func, "deep", 0)
    # 默认阻断
    block: bool = getattr(func, "block", True)

    # 注册
    for s in states:
        s.on_cmd(cmds, app, deep, block)(func)

    return func


driver = get_driver()


@driver.on_startup
async def startup():
    # 注册所有回调
    for app in app_list:
        for func in app.funcs:
            regist_func(app, func)

    if ayaka_root_config.debug:
        s = json.dumps(
            root_state.dict(), ensure_ascii=0,
            indent=4, default=repr
        )
        path = ayaka_data_path / "all_state.json"
        with path.open("w+", encoding="utf8") as f:
            f.write(s)

on_message(priority=20, block=False, handlers=[deal_event])
