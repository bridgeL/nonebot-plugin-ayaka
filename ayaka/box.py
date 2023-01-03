from math import ceil
from typing import Callable, Type, TypeVar
from typing_extensions import Self
from collections import defaultdict
from nonebot.matcher import current_bot, current_event, current_matcher
from nonebot.params import _command_arg

from .helpers import _command_args, ensure_list, pack_messages
from .lazy import get_driver, on_command, on_message, Rule, GroupMessageEvent, PrivateMessageEvent, Message, MessageSegment, Bot, BaseModel


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
listeners: dict[int, list[int]] = {}
'''监听列表，将私聊消息转发给当前正监听它的若干个群聊'''
LISTEN = on_message(block=False)
'''处理监听转发的matcher'''


class AyakaGroup:
    '''群组

    属性:

        state: group当前所处状态，初始值为idle

        current_box_name: group当前正在运行的box的名字

        cache: group当前缓存的数据，不会随事件结束而清除

        group_id: 群组qq号
    '''

    def __init__(self, group_id: int) -> None:
        self.state = ""
        self.current_box_name = ""
        self.cache = defaultdict(dict)
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
    def _func(*args, **kwargs):
        data = current_matcher.get().state
        key = f"ayaka_{func.__name__}"
        if key not in data:
            data[key] = func()
        return data[key]
    return _func


class AyakaBox:
    '''盒子，通过盒子使用ayaka的大部分特性

    属性:

        name: box的名字，应与插件名字一致

        immediates: on_immediate注册状态记录

        更多计算属性请查询api文档

    示例代码1:
    ```
        from ayaka.box import AyakaBox
        from nonebot import on_message

        box = AyakaBox("测试")
        matcher = on_message(rule=box.rule())

        @matcher.handle()
        async def matcher_handle():
            print(box.group, box.group.group_id)
    ```
    示例代码2:
    ```
        from ayaka.box import AyakaBox

        box = AyakaBox("测试")
        matcher = box.create_text_matcher()

        @matcher.handle()
        async def matcher_handle():
            print(box.group, box.group.group_id)
    ```
    '''

    def __new__(cls: type[Self], name: str, *args, **kwargs) -> Self:
        b = get_box(name)
        if b:
            return b
        return super().__new__(cls)

    def __init__(self, name: str, allow_same: bool = False) -> None:
        '''初始化box对象

        参数:

            name: box的名字，需保证其唯一性，如果重名，则会返回重名的box

            allow_same: 允许重名，默认为False，当出现重名时抛出异常

            注意: 若要使用allow_same，则必须保证所有重名box均设置该项为True，否则可能会由于加载顺序的随机性，导致重名异常

        异常:

            已有重名box
        '''
        if get_box(name):
            if not allow_same:
                raise Exception(f"已有重名box: {name}")
            return

        self.name = name
        self.immediates = set()
        self._help = ""
        self._helps: dict[str, list] = {}
        box_list.append(self)

    # ---- 便捷属性 ----
    @property
    def help(self):
        '''box的帮助'''
        return self._help

    @help.setter
    def help(self, value):
        '''设置box的帮助'''
        self._help = str(value).strip()

    @property
    def bot(self):
        '''当前bot'''
        bot = current_bot.get()
        assert isinstance(bot, Bot)
        return bot

    @property
    def event(self):
        '''当前事件'''
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
        return get_group(self.event.group_id)

    @property
    def state(self):
        '''当前群组状态'''
        return self.group.state

    @property
    def cache(self):
        '''当前群组缓存：当前正在处理的群组的缓存数据空间中，分配给该box.name的独立字典'''
        return self.group.cache[self.name]

    @property
    def bot_id(self):
        '''当前bot id'''
        return int(self.bot.self_id)

    @property
    def group_id(self):
        '''当前group id'''
        return self.event.group_id

    @property
    def user_id(self):
        '''当前user id'''
        return self.event.user_id

    @property
    @cached
    def user_name(self):
        '''当前群消息的发送者群名片或qq昵称'''
        return self.event.sender.card or self.event.sender.nickname

    @property
    def arg(self):
        '''去除了命令之后的消息'''
        arg = _command_arg(self.matcher_state)
        if arg is None:
            arg = self.event.message
        return arg

    @property
    @cached
    def args(self):
        '''去除了命令之后的消息，再根据分割符进行分割'''
        return _command_args(self.arg)

    @property
    def all_help(self):
        '''全部帮助'''
        items = [f"[{self.name}]"]
        if self.help:
            items.append(self.help)
        for state, infos in self._helps.items():
            items.append(f"[{state}]")
            items.extend(infos)
        return "\n".join(items)

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
        ```
        '''
        if state in ["", "*"]:
            raise Exception("state不可为空字符串或*")
        self.group.state = state

        if state in self.immediates:
            event = GroupMessageEvent(
                **self.event.dict(exclude={"message", "raw_message"}),
                message=Message(on_immediate_cmd),
                raw_message=on_immediate_cmd
            )
            await self.bot.handle_event(event)

    async def start(self, state: str = "idle"):
        '''启动当前应用，启动后应用状态默认为idle

        参数: 

            state: 新状态

        异常:

            state不可为空字符串或*
        '''
        if state in ["", "*"]:
            raise Exception("state不可为空字符串或*")
        self.group.state = state
        self.group.current_box_name = self.name
        await self.send(f"已启动应用[{self.name}]")

    async def close(self):
        '''关闭当前应用'''
        self.group.current_box_name = ""
        await self.send(f"已关闭应用[{self.name}]")

    # ---- 兼容性 ----
    def rule(self, states: str | list[str] = []):
        '''返回一个检查state的Rule对象

        参数:

            states: 命令状态，为空时意味着无状态命令

        返回:

            Rule对象

        示例代码:
        ```
            from ayaka.box import AyakaBox
            from nonebot import on_command

            box = AyakaBox("测试")
            # 仅在群组运行当前应用，且状态为test1或test2时
            # m1才能被命令hh触发
            m1 = on_command(cmd="hh", rule=box.rule(states=["test1", "test2"]))

            # 仅在群组运行当前应用时。m2才能被命令hh触发
            m2 = on_command(cmd="hh", rule=box.rule())

            # 无视box的任何规定，m3总能被命令hh触发
            m3 = on_command(cmd="hh")

            # 请注意三者的区别
        ```
        '''
        states = ensure_list(states)

        def ayaka_state_checker(event: GroupMessageEvent):
            group = get_group(event.group_id)
            if not states:
                return not group.current_box_name
            if group.current_box_name != self.name:
                return False
            if "*" in states:
                return True
            return group.state in states

        return Rule(ayaka_state_checker)

    # ---- on_xxx ----
    def on_cmd(self, cmds: str | list[str], states: str | list[str] = [], **params):
        '''注册命令处理回调

        参数:

            cmds: 注册命令，不可为空

            states: 命令状态，*意味着对所有状态生效，为空时意味着无状态命令

            params: 其他参数，参考nonebot.on_command

        返回:

            装饰器

        异常:

            cmds不可为空

        示例代码:
        ```
            from ayaka.box import AyakaBox

            box = AyakaBox("测试")

            # 仅在群组正在运行当前应用，且状态为test1或test2时
            # matcher_handle_1才会被命令hh触发
            @box.on_cmd(cmds="hh", states=["test1", "test2"])
            async def matcher_handle_1():
                pass

            # 仅在群组没有运行任何应用时，matcher_handle_2才会被命令hh触发
            @box.on_cmd(cmds="hh")
            async def matcher_handle_2():
                pass

            # 请注意其与on_command("hh")的区别
            # on_command("hh")无视box这些规定，只要检测到hh命令就会触发
        ```
        '''
        if not cmds:
            raise Exception("cmds不可为空")
        cmds = ensure_list(cmds)
        states = ensure_list(states)
        rule = self.rule(states) & params.pop("rule", None)

        def decorator(func):
            matcher = on_command(
                cmd=cmds[0],
                aliases=set(cmds[1:]),
                rule=rule,
                **params
            )
            matcher.handle()(func)
            self._add_help(cmds, states, func)
            return func
        return decorator

    def on_text(self, states: str | list[str] = [], **params):
        '''注册消息处理回调

        参数:

            states: 命令状态，*意味着对所有状态生效，为空时意味着无状态命令

            params: 其他参数，参考nonebot.on_message

        返回:

            装饰器
        '''
        states = ensure_list(states)
        rule = self.rule(states) & params.pop("rule", None)
        params.setdefault("block", False)

        def decorator(func):
            matcher = on_message(rule=rule, **params)
            matcher.handle()(func)
            self._add_help([], states, func)
            return func
        return decorator

    def on_immediate(self, state: str):
        '''注册立即处理回调

        参数:

            state: 注册状态，不可为*

        返回:

            装饰器

        异常:

            state不可以为*

        此注册方法很特殊，其回调在box.state变为指定的state时立刻执行
        '''
        if state == "*":
            raise Exception("state不可以为*")

        def decorator(func):
            self.immediates.add(state)
            self.on_cmd(cmds=["on_immediate"], states=[state])(func)
            return func
        return decorator

    # ---- 快捷命令 ----
    def set_start_cmds(self, cmds: str | list[str]):
        '''设置启动命令'''
        self.on_cmd(cmds=cmds)(self.start)

    def set_close_cmds(self, cmds: str | list[str]):
        '''设置关闭命令'''
        self.on_cmd(cmds=cmds, states="*")(self.close)

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
            matcher = box.create_text_matcher()

            class Data(BaseModel):
                cnt: int = 0

            @matcher.handle()
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

    def get_data(self, cls: Type[T_BaseModel], key: str = None) -> T_BaseModel:
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
            matcher = box.create_text_matcher()

            class Data(BaseModel):
                cnt: int = 0

            @matcher.handle()
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
