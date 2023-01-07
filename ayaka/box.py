'''
ayaka 盒子

ayaka的核心模块
'''
from math import ceil
from typing import Callable, TypeVar
from starlette._utils import is_async_callable
from nonebot.rule import CommandRule
from nonebot.matcher import Matcher, current_bot, current_event, current_matcher
from nonebot.params import _command_arg, _raw_command

from .helpers import Timer, _command_args, ensure_list, pack_messages, run_in_startup
from .lazy import Rule, GroupMessageEvent, PrivateMessageEvent, MessageEvent, Message, MessageSegment, Bot, BaseModel, get_driver, on_command, on_message, logger


driver = get_driver()
'''驱动器'''
on_immediate_cmd = list(driver.config.command_start)[0] + "on_immediate"
'''用来实现on_immediate效果的特殊命令'''
T = TypeVar("T")
'''任意类型'''
T_BaseModel = TypeVar("T_BaseModel", bound=BaseModel)
'''BaseModel的子类'''
group_list: list["AyakaGroup"] = []
'''群组列表'''
box_list: list["AyakaBox"] = []
'''box列表'''
func_list: list["AyakaDelayMatcher"] = []
'''AyakaDelayMatcher列表'''
listeners: dict[int, list[int]] = {}
'''监听列表，将私聊消息转发给当前正监听它的若干个群聊'''
LISTEN = on_message(block=False)
'''处理监听转发的matcher'''


class AyakaDelayMatcher:
    def __init__(self, module_name, func, cmds, rule, priority, params) -> None:
        if not module_name:
            module_name = func.__module__
        self.module_name = module_name
        self.func = func
        self.cmds = cmds
        self.rule = rule
        self.priority = priority
        self.params = params
        func_list.append(self)

    def create(self):
        '''生成所有matcher'''
        if self.cmds:
            matcher = on_command(
                cmd=self.cmds[0],
                aliases=set(self.cmds[1:]),
                rule=self.rule,
                priority=self.priority,
                **self.params
            )
            matcher.module_name = self.module_name
            matcher.handle()(self.func)
        else:
            matcher = on_message(
                rule=self.rule,
                priority=self.priority,
                **self.params
            )
            matcher.module_name = self.module_name
            matcher.handle()(self.func)


@run_in_startup
async def create_all_matcher():
    '''加速插件加载'''
    logger.opt(colors=True).info(
        "<y>ayaka</y> 正在创建matcher，可能会收到Duplicated prefix rule警告，而这是正常的")

    t = Timer(show=False)
    with t:
        for func in func_list:
            func.create()
    logger.opt(colors=True).info(
        f"<y>ayaka</y> 已成功创建全部matchers，耗时{t.diff:.2f}s")


class AyakaGroup:
    '''群组

    属性:

        current_box: group当前正在运行的box

        group_id: 群组qq号
    '''

    def __init__(self, group_id: int) -> None:
        self.current_box: AyakaBox | None = None
        self.group_id = group_id


def get_group(group_id: int):
    '''获得群组对象，若不存在则自动新增'''
    for group in group_list:
        if group.group_id == group_id:
            return group
    group = AyakaGroup(group_id)
    group_list.append(group)
    return group


def get_box(name: str):
    '''获得指定名字的box

    参数:

        name: box的名字

    返回:

        box 或 None
    '''

    for box in box_list:
        if box.name == name:
            return box


def cached(func):
    '''在matcher.state中缓存内容

    注意：如果和property装饰器配合使用，cached必须位于property装饰器下方'''
    if is_async_callable(func):
        async def _func(*args, **kwargs):
            matcher_state = current_matcher.get().state
            matcher_state.setdefault("ayaka", {})
            data = matcher_state["ayaka"]

            key = func.__name__
            if key not in data:
                data[key] = await func(*args, **kwargs)
            return data[key]
    else:
        def _func(*args, **kwargs):
            matcher_state = current_matcher.get().state
            matcher_state.setdefault("ayaka", {})
            data = matcher_state["ayaka"]

            key = func.__name__
            if key not in data:
                data[key] = func(*args, **kwargs)
            return data[key]

    return _func


class AyakaBox:
    '''盒子，通过盒子使用ayaka的大部分特性

    属性:

        name: box的名字，应与插件名字一致

        immediates: on_immediate注册状态记录

        priority: 优先级

        更多计算属性请查询api文档

    示例代码1:
    ```
        from ayaka.box import AyakaBox
        from nonebot import on_command

        box = AyakaBox("测试")
        matcher = on_command("test", rule=box.rule(states="yes"))

        @matcher.handle()
        async def matcher_handle():
            print(box.group, box.group.group_id)
    ```
    示例代码2:
    ```
        from ayaka.box import AyakaBox

        box = AyakaBox("测试")

        @box.on_cmd(cmds="test", states="yes")
        async def matcher_handle():
            print(box.group, box.group.group_id)
    ```
    '''

    def __new__(cls, name: str, *args, **kwargs):
        b = get_box(name)
        if b:
            return b
        return super().__new__(cls)

    def __init__(self, name: str, allow_same: bool = False, priority: int = 5) -> None:
        '''初始化box对象

        参数:

            name: box的名字，需保证其唯一性，如果重名，则会返回重名的box

            allow_same: 允许重名，默认为False，当出现重名时抛出异常

            注意: 若要使用allow_same，则必须保证所有重名box均设置该项为True，否则可能会由于加载顺序的随机性，导致重名异常

            priority: 注册命令的优先级；注册消息的优先级为priority+1

        异常:

            已有重名box
        '''
        if get_box(name):
            if not allow_same:
                raise Exception(f"已有重名box: {name}")
            return

        self.name = name
        self.immediates = set()
        self.priority = priority
        self._intro = ""
        self._helps: dict[str, list] = {}
        self._state_dict: dict[int, str] = {}
        self._cache_dict: dict[int, dict] = {}
        box_list.append(self)
        logger.opt(colors=True).debug(f"已生成盒子 <c>{name}</c>")

    # ---- 便捷属性 ----
    @property
    def bot(self):
        '''当前bot'''
        bot = current_bot.get()
        assert isinstance(bot, Bot)
        return bot

    @property
    def event(self):
        '''当前消息事件'''
        event = current_event.get()
        assert isinstance(event, MessageEvent)
        return event

    @property
    def group_event(self):
        '''当前群聊消息事件'''
        event = current_event.get()
        assert isinstance(event, GroupMessageEvent)
        return event

    @property
    def matcher(self):
        '''当前nb匹配器'''
        return current_matcher.get()

    @property
    def matcher_state(self):
        '''当前nb事务处理的state数组'''
        return self.matcher.state

    @property
    def message(self):
        '''当前群聊消息'''
        return self.event.message

    @property
    @cached
    def group(self):
        '''当前群组'''
        return get_group(self.group_event.group_id)

    @property
    def state(self):
        '''当前盒子状态'''
        self._state_dict.setdefault(self.group_id, "idle")
        return self._state_dict[self.group_id]

    @state.setter
    def state(self, k: str):
        '''设置盒子状态'''
        self._state_dict[self.group_id] = k

    @property
    def cache(self):
        '''当前数据缓存'''
        self._cache_dict.setdefault(self.group_id, {})
        return self._cache_dict[self.group_id]

    @property
    def bot_id(self):
        '''当前bot id'''
        return int(self.bot.self_id)

    @property
    def group_id(self):
        '''当前group id'''
        return self.group_event.group_id

    @property
    def user_id(self):
        '''当前user id'''
        return self.event.user_id

    @property
    def user_name(self):
        '''当前群消息的发送者群名片或qq昵称'''
        return self.event.sender.card or self.event.sender.nickname

    @property
    @cached
    def cmd(self):
        '''当前命令'''
        if check_cmd_matcher(self.matcher):
            return str(_raw_command(self.matcher_state))
        else:
            return ""

    @property
    @cached
    def arg(self):
        '''去除了命令之后的消息'''
        if self.cmd:
            return _command_arg(self.matcher_state)
        else:
            return self.message

    @property
    @cached
    def args(self):
        '''去除了命令之后的消息，再根据分割符进行分割'''
        return _command_args(self.arg)

    @property
    def help(self):
        '''box的帮助'''
        items = [f"[{self.name}]"]
        if self._intro:
            items.append(self._intro)
        items.extend(self._helps.get("no_state", []))
        for state, infos in self._helps.items():
            if state == "no_state":
                continue
            items.append(f"[{state}]")
            items.extend(infos)
        return "\n".join(items)

    @help.setter
    def help(self, value):
        '''设置box的帮助'''
        self._intro = str(value).strip()

    # ---- 添加帮助 ----
    def _add_help(self, cmds: list[str], states: list[str], func=None):
        '''添加帮助

        参数:

            cmds: 命令

            states: 状态

            func: 回调
        '''
        if "on_immediate" in cmds:
            return
        info = "- "
        if cmds:
            info += "/".join(cmds) + " "
        else:
            info += "<任意文字> "
        if func and func.__doc__:
            info += func.__doc__
        if not states:
            states = ["no_state"]
        for state in states:
            if state not in self._helps:
                self._helps[state] = [info]
            else:
                self._helps[state].append(info)

    # ---- 设置状态 ----
    async def set_state(self, state: str):
        '''修改当前群组状态

        参数: 

            state: 新状态

        异常:

            state不可为空字符串或*
        '''
        if state in ["", "*"]:
            raise Exception("state不可为空字符串或*")
        self.state = state

        if state in self.immediates:
            event = GroupMessageEvent(
                **self.group_event.dict(exclude={"message", "raw_message"}),
                message=Message(on_immediate_cmd),
                raw_message=on_immediate_cmd
            )
            await self.bot.handle_event(event)

    async def start(self, state: str = "idle"):
        '''启动当前盒子，启动后盒子状态默认为idle

        参数: 

            state: 新状态

        异常:

            state不可为空字符串或*
        '''
        self.group.current_box = self
        await self.set_state(state)
        await self.send(f"已启动盒子[{self.name}]")

    async def close(self):
        '''关闭当前盒子'''
        name = self.group.current_box.name
        self.group.current_box = None
        await self.send(f"已关闭盒子[{name}]")

    # ---- 兼容性 ----
    def rule(self, states: str | list[str] = []):
        '''返回一个检查state的Rule对象

        参数:

            states: 命令状态，为空时意味着注册群聊闲置状态时的命令

        返回:

            Rule对象

        示例代码:
        ```
            from ayaka.box import AyakaBox
            from nonebot import on_command

            box = AyakaBox("测试")
            # 仅在群组运行当前盒子，且状态为test1或test2时
            # m1才能被命令hh触发
            m1 = on_command(cmd="hh", rule=box.rule(states=["test1", "test2"]))

            # 仅在群组运行当前盒子时。m2才能被命令hh触发
            m2 = on_command(cmd="hh", rule=box.rule())

            # 无视box的任何规定，m3总能被命令hh触发
            m3 = on_command(cmd="hh")

            # 请注意以上三者的区别

            @m1.handle()
            async def func():
                # 以下两种发送方式等价
                await box.send("ok")
                await m1.send("ok")

                # box还提供了发送群聊合并转发消息的方法
                await box.send_many(["1","2","3"])
        ```
        '''
        states = ensure_list(states)

        def ayaka_state_checker(event: GroupMessageEvent):
            group_id = event.group_id
            group = get_group(group_id)
            # 群聊闲置状态时响应
            if not states:
                return not group.current_box
            # 如果群聊被独占，则屏蔽其他盒子
            if group.current_box != self:
                return False
            # 必定响应*
            if "*" in states:
                return True
            # 当前盒子状态是否符合要求
            if group_id not in self._state_dict:
                return False
            # 当前盒子状态是否符合要求
            return self._state_dict[group_id] in states

        return Rule(ayaka_state_checker)

    # ---- on_xxx ----
    def _on(self, cmds: str | list[str] = [], states: str | list[str] = [], always: bool = False, module_name: str = "", priority: int = 5, **params):
        '''注册命令处理回调（基础）

        参数:

            cmds: 注册命令，为空时视为消息触发

            states: 命令状态，*意味着对所有状态生效，为空时意味着注册群聊闲置状态时的命令

            always: 默认为False，设置为True时，意为总是触发该命令，其与注册群聊闲置状态时的命令不同

            module_name: 生成的matcher的module_name

            priority：生成的matcher的priority

            params: 其他参数，参考nonebot.on_command

        返回:

            装饰器

        异常:

            state不可为空字符串
        '''
        cmds = ensure_list(cmds)
        states = ensure_list(states)
        rule = params.pop("rule", None)
        if "" in states:
            raise Exception("state不可为空字符串")
        if not always:
            rule = self.rule(states) & rule

        def decorator(func):
            self._add_help(cmds, states, func)
            AyakaDelayMatcher(module_name, func, cmds, rule, priority, params)
            return func
        return decorator

    def on_cmd(self, cmds: str | list[str], states: str | list[str] = [], always: bool = False, **params):
        '''注册命令处理回调

        参数:

            cmds: 注册命令，为空时视为消息触发

            states: 命令状态，*意味着对所有状态生效，为空时意味着注册群聊闲置状态时的命令

            always: 默认为False，设置为True时，意为总是触发该命令，其与注册群聊闲置状态时的命令不同

            params: 其他参数，参考nonebot.on_command

        返回:

            装饰器

        异常:

            state不可为空字符串

        示例代码:
        ```
            from ayaka.box import AyakaBox

            box = AyakaBox("测试")

            # 仅在群组正在运行当前盒子，且状态为test1或test2时
            # matcher_handle_1才会被命令hh触发
            @box.on_cmd(cmds="hh", states=["test1", "test2"])
            async def matcher_handle_1():
                pass

            # 仅在群组没有运行任何盒子时，matcher_handle_2才会被命令hh触发
            @box.on_cmd(cmds="hh")
            async def matcher_handle_2():
                pass

            # 请注意其与on_command("hh")的区别
            # on_command("hh")无视box这些规定，只要检测到hh命令就会触发
        ```
        '''
        params.setdefault("block", True)
        priority = params.pop("priority", self.priority)
        return self._on(cmds=cmds, states=states, always=always, priority=priority, **params)

    def on_text(self, states: str | list[str] = [], always: bool = False, **params):
        '''注册消息处理回调

        参数:

            states: 命令状态，*意味着对所有状态生效，为空时意味着注册群聊闲置状态时的命令

            always: 默认为False，设置为True时，意为总是触发该命令，其与注册群聊闲置状态时的命令不同

            params: 其他参数，参考nonebot.on_message

        返回:

            装饰器

        异常:

            state不可为空字符串
        '''
        params.setdefault("block", False)
        priority = params.pop("priority", self.priority+1)
        return self._on(states=states, always=always, priority=priority, **params)

    def on_immediate(self, state: str):
        '''注册立即处理回调

        参数:

            state: 注册状态，不可为空字符串或*

        返回:

            装饰器

        异常:

            state不可为空字符串或*

        此注册方法很特殊，其回调在box.state变为指定的state时立刻执行
        '''
        if state in ["", "*"]:
            raise Exception("state不可为空字符串或**")
        self.immediates.add(state)
        return self._on(cmds="on_immediate", states=state, priority=self.priority, block=True, module_name=self.name)

    # ---- 快捷命令 ----
    def set_start_cmds(self, cmds: str | list[str]):
        '''设置启动命令'''
        @self._on(cmds=cmds, module_name=self.name)
        async def start():
            '''启动盒子'''
            await self.start()
            await self.send_help()

    def set_close_cmds(self, cmds: str | list[str]):
        '''设置关闭命令'''
        @self._on(cmds=cmds, states="*", module_name=self.name)
        async def close():
            '''关闭盒子'''
            await self.close()

    # ---- cache ----
    def remove_data(self, key_or_obj: str | T_BaseModel):
        '''从当前群组的缓存移除指定的键-值对

        参数:

            key: 键名或BaseModel对象，如果是BaseModel对象，则自动取其类的名字作为键名

        异常:

            参数类型错误，必须是字符串或BaseModel对象

        示例代码:
        ```
            from pydantic import BaseModel
            from ayaka.box import AyakaBox

            box = AyakaBox("测试")

            class Data(BaseModel):
                cnt: int = 0

            @box.on_text()
            async def matcher_handle():
                data = box.load_data_from_cache(Data)
                print(box.cache)
                box.remove_data_from_cache(data)
                print(box.cache)
        ```
        '''
        if isinstance(key_or_obj, str):
            key = key_or_obj
        elif isinstance(key_or_obj, BaseModel):
            key = key_or_obj.__class__.__name__
        else:
            raise Exception("参数类型错误，必须是字符串或BaseModel对象")
        self.cache.pop(key, None)

    def get_arbitrary_data(self, key: str, default_factory: Callable[[], T]) -> T:
        '''从当前群组的缓存中加载指定key下的任意类型对象，即self.cache[key]，若不存在则自动通过default_factory()创建

        参数:

            key: 键名

            default_factory: 若key不存在，则通过default_factory()方法创建默认值，保存到cache中并返回

        返回:

            self.cache[key]
        '''
        if key not in self.cache:
            self.cache[key] = default_factory()
        return self.cache[key]

    def get_data(self, cls: type[T_BaseModel], key: str = None) -> T_BaseModel:
        '''从当前群组的缓存中加载指定的BaseModel对象

        参数:

            cls: BaseModel类

            key: 键名，为空时使用cls.__name__作为键名

        返回:

            BaseModel对象

        示例代码:
        ```
            from pydantic import BaseModel
            from ayaka.box import AyakaBox

            box = AyakaBox("测试")

            class Data(BaseModel):
                cnt: int = 0

            @box.on_text()
            async def matcher_handle():
                data = box.load_data_from_cache(Data)
                data.cnt += 1
                print(data.cnt)
        ```
        '''
        if key is None:
            key = cls.__name__
        if key not in self.cache:
            data = cls()
            self.cache[key] = data
            return data
        return self.cache[key]

    # ---- 快捷发送 ----
    async def send(self, message: Message | MessageSegment | str):
        '''发送消息'''
        return await self.matcher.send(message)

    async def send_many(self, messages: list[Message | MessageSegment | str]):
        '''发送合并转发消息'''
        # 分割长消息组（不可超过100条
        div_len = 100
        div_cnt = ceil(len(messages) / div_len)
        for i in range(div_cnt):
            msgs = pack_messages(
                user_id=self.bot_id,
                user_name="Ayaka Bot",
                messages=messages[i*div_len: (i+1)*div_len]
            )
            await self.bot.send_group_forward_msg(group_id=self.group_id, messages=msgs)

    async def send_help(self):
        '''发送自身帮助'''
        await self.send(self.help)

    # ---- 监听私聊 ----
    def add_listener(self, user_id: int):
        '''为该群组添加对指定私聊的监听'''
        if user_id not in listeners:
            listeners[user_id] = []
        listeners[user_id].append(self.group_id)

    def remove_listener(self, user_id: int = 0):
        '''默认移除该群组对其他私聊的所有监听'''
        if user_id == 0:
            uids = list(listeners.keys())
            for uid in uids:
                self.remove_listener(uid)
            return

        if self.group_id in listeners[user_id]:
            if len(listeners[user_id]) == 1:
                listeners.pop(user_id)
            else:
                listeners[user_id].remove(self.group_id)


@LISTEN.handle()
async def listener_handle(bot: Bot, event: PrivateMessageEvent):
    if event.user_id in listeners:
        _event = GroupMessageEvent(
            **event.dict(exclude={"message_type"}),
            group_id=0,
            message_type="group"
        )

        for group_id in listeners[event.user_id]:
            _event.group_id = group_id
            await bot.handle_event(_event)


def check_cmd_matcher(matcher: Matcher):
    '''探测一个matcher是否是on_command注册的'''
    for c in matcher.rule.checkers:
        if isinstance(c.call, CommandRule):
            return True
    return False
