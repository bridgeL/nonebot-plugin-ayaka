from math import ceil
from typing import Type, TypeVar
from pydantic import BaseModel
from collections import defaultdict

from nonebot import get_driver, on_command, on_message
from nonebot.internal.rule import Rule
from nonebot.internal.matcher import current_bot, current_event, current_matcher
from nonebot.params import _command_arg
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, MessageSegment, Bot, PrivateMessageEvent

from .helpers import StrOrMsgList

driver = get_driver()
on_immediate_cmd = list(driver.config.command_start)[0] + "on_immediate"
'''用来实现on_immediate效果的特殊命令'''
T_BaseModel = TypeVar("T_BaseModel", bound=BaseModel)
'''BaseModel的子类'''


class AyakaGroup:
    '''群组

    属性:
        state: group当前所处状态，初始值为idle
        current_box_name: group当前正在运行的box的名字
        cache: group当前缓存的数据，不会随事件结束而清除
        group_id: 群组qq号
    '''

    def __init__(self, group_id: int) -> None:
        self.state = "idle"
        self.current_box_name = ""
        self.cache = defaultdict(dict)
        self.group_id = group_id


group_list: list[AyakaGroup] = []
'''群组列表'''


def get_group(group_id: int):
    '''获得群组对象，若不存在则自动新增'''
    for group in group_list:
        if group.group_id == group_id:
            return group
    group = AyakaGroup(group_id)
    group_list.append(group)
    return group


def cached(func):
    '''在state中缓存box的属性'''
    def new_func(*args, **kwargs):
        data = current_matcher.get().state

        if "ayaka_box" not in data:
            data["ayaka_box"] = {}
        data = data["ayaka_box"]

        name = func.__name__
        if name not in data:
            data[name] = func(*args, **kwargs)
        return data[name]

    return new_func


listeners: dict[int, list[int]] = {}


class AyakaBox:
    '''盒子，通过盒子使用ayaka的大部分特性

    属性:
        name: box的名字，应与插件名字一致
        immediates: on_immediate注册状态记录

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

    def __init__(self, name: str) -> None:
        '''初始化box对象

        参数:
            name: box的名字，需保证其唯一性
        '''
        self.name = name
        self.immediates = set()

    # ---- 便捷属性 ----
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
    def user_name(self):
        '''当前群消息的发送者群名片或qq昵称'''
        return self.event.sender.card or self.event.sender.nickname

    @property
    def arg(self):
        '''去除了命令之后的消息'''
        return _command_arg(current_matcher.get().state)

    @property
    @cached
    def args(self):
        '''去除了命令之后的消息，再根据分割符进行分割'''
        return StrOrMsgList.create(self.arg)

    # ---- 设置状态 ----
    async def set_state(self, state: str = "idle"):
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

        if state == "idle":
            self.group.current_box_name = ""
        else:
            self.group.current_box_name = self.name

        if state in self.immediates:
            event = GroupMessageEvent(
                **self.event.dict(exclude={"message", "raw_message"}),
                message=Message(on_immediate_cmd),
                raw_message=on_immediate_cmd
            )
            await self.bot.handle_event(event)

    async def reset_state(self):
        '''重置当前群组状态为idle'''
        return await self.set_state()

    async def start(self, state: str = "menu"):
        '''启动当前应用，启动后应用状态默认为menu'''
        await self.set_state(state)
        await self.send(f"已启动应用[{self.name}]")

    async def close(self):
        '''关闭当前应用'''
        await self.reset_state()
        await self.send(f"已关闭应用[{self.name}]")

    # ---- 兼容性 ----
    def rule(self, *states: str):
        '''返回一个检查state的Rule对象

        参数:
            states: 注册状态

        返回:
            Rule对象

        示例代码:
        ```
            from ayaka.box import AyakaBox
            from nonebot import on_message

            box = AyakaBox("测试")
            # 该matcher在群组处于test1或test2状态下时才能触发
            matcher = on_message(box.rule("test1", "test2"))
        ```
        '''
        if not states:
            states = ["idle"]

        def checker(event: GroupMessageEvent):
            group = get_group(event.group_id)
            if group.state == "idle":
                return "idle" in states
            if group.current_box_name != self.name:
                return False
            if "*" in states:
                return True
            return group.state in states

        return Rule(checker)

    def create_cmd_matcher(self, cmds: list, states: list = ["idle"],  **params):
        '''创建命令matcher

        参数:
            cmds: 注册命令
            states: 注册状态，*意味着对所有状态生效（除idle）
            params: 其他参数，参考nonebot.on_command

        返回:
            nonebot.matcher.Matcher对象

        异常:
            cmds不可为空

        示例代码:
        ```
            from ayaka.box import AyakaBox

            box = AyakaBox("测试")
            matcher = box.create_cmd_matcher(cmds=["hh"], states=["test"])

            @matcher.handle()
            async def matcher_handle():
                pass
        ```
        '''
        if not cmds:
            raise Exception("cmds不可为空")
        rule = self.rule(*states) & params.pop("rule", None)
        matcher = on_command(cmd=cmds[0], aliases=set(
            cmds[1:]), rule=rule, **params)
        matcher.ayaka_flag = True
        return matcher

    def create_text_matcher(self, states: list = ["idle"],  **params):
        '''创建消息matcher

        参数:
            states: 注册状态，*意味着对所有状态生效（除idle）
            params: 其他参数，参考nonebot.on_message

        返回:
            nonebot.matcher.Matcher对象
        '''
        rule = self.rule(*states) & params.pop("rule", None)
        params.setdefault("block", False)
        matcher = on_message(rule=rule, **params)
        matcher.ayaka_flag = True
        return matcher

    # ---- on_xxx ----
    def on_cmd(self, cmds: list, states: list = ["idle"], **params):
        '''注册命令处理回调

        参数:
            cmds: 注册命令
            states: 注册状态，*意味着对所有状态生效（除idle）
            params: 其他参数，参考nonebot.on_command

        返回:
            装饰器

        异常:
            cmds不可为空

        示例代码:
        ```
            from ayaka.box import AyakaBox

            box = AyakaBox("测试")

            @box.on_cmd(cmds=["hh"], states=["test"])
            async def matcher_handle():
                pass
        ```
        '''
        if not cmds:
            raise Exception("cmds不可为空")
        rule = self.rule(*states) & params.pop("rule", None)

        def decorator(func):
            matcher = on_command(
                cmd=cmds[0],
                aliases=set(cmds[1:]),
                rule=rule,
                **params
            )
            matcher.handle()(func)
            matcher.ayaka_flag = True
            return func
        return decorator

    def on_text(self, states: list = ["idle"], **params):
        '''注册消息处理回调

        参数:
            states: 注册状态，*意味着对所有状态生效（除idle）
            params: 其他参数，参考nonebot.on_message

        返回:
            装饰器
        '''
        rule = self.rule(*states) & params.pop("rule", None)
        params.setdefault("block", False)

        def decorator(func):
            matcher = on_message(rule=rule, **params)
            matcher.handle()(func)
            matcher.ayaka_flag = True
            return func
        return decorator

    def on_immediate(self, state: str):
        '''注册立即处理回调

        参数:
            state: 注册状态，不可为*

        返回:
            装饰器

        异常:
            state不可以为idle或*

        此注册方法很特殊，其回调在box.state变为指定的state时立刻执行
        '''
        if state in ["idle", "*"]:
            raise Exception("state不可以为idle或*")

        def decorator(func):
            self.immediates.add(state)
            self.on_cmd(cmds=["on_immediate"], states=[state])(func)
            return func
        return decorator

    # ---- 快捷命令 ----
    def set_start_cmds(self, *cmds: str):
        '''设置启动命令，启动后，插件进入menu状态'''
        self.on_cmd(cmds=cmds)(self.start)

    def set_close_cmds(self, *cmds: str):
        '''设置关闭命令'''
        self.on_cmd(cmds=cmds, states=["*"])(self.close)

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
                self.bot_id,
                messages[i*div_len: (i+1)*div_len]
            )
            await self.bot.call_api("send_group_forward_msg", group_id=self.group_id, messages=msgs)

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


def pack_messages(bot_id, messages):
    '''转换为cqhttp node格式'''
    data = [
        MessageSegment.node_custom(
            user_id=bot_id,
            nickname="Ayaka Bot",
            content=str(m)
        )
        for m in messages
    ]
    return data


matcher = on_message(block=False)


@matcher.handle()
async def listener_handle(bot: Bot, event: PrivateMessageEvent):
    if event.user_id in listeners:
        event2 = GroupMessageEvent(**event.dict(exclude={"message_type"}), group_id=0, message_type="group")
        for group_id in listeners[event.user_id]:
            event2.group_id = group_id
            await bot.handle_event(event2)
