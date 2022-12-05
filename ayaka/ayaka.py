'''ayaka核心'''
import inspect
from math import ceil
from pathlib import Path
from loguru import logger
from typing import List, Dict, Literal, Union

from .ayaka_parser import parser
from .config import ayaka_root_config, create_ayaka_plugin_config_base
from .constant import _bot, _event, _group, _arg, _args, _message, _cmd, app_list, private_listener_dict, get_bot
from .deal import deal_event
from .group import get_group
from .storage import AyakaStorage
from .driver import on_message, MessageSegment
from .state import AyakaState, root_state


class AyakaApp:
    def __repr__(self) -> str:
        return f"AyakaApp({self.name}, {self.state})"

    def __init__(self, name: str) -> None:
        self.path = Path(inspect.stack()[1].filename)

        for app in app_list:
            if app.name == name:
                raise Exception(
                    f"应用{app.name} 重复注册，已忽略注册时间更晚的应用！\n{app.path}(最早注册)\n{self.path}(被忽略)")

        self.name = name
        self._help: Dict[str, List[str]] = {}
        self.storage = AyakaStorage(self)
        self.parser = parser
        self.BaseConfig = create_ayaka_plugin_config_base(name)
        self.ayaka_root_config = ayaka_root_config

        app_list.append(self)
        if ayaka_root_config.debug:
            print(self)

    # @property
    # def intro(self):
    #     '''获取介绍，也就是init状态下的帮助'''
    #     helps = self._help.get(INIT_STATE, ["没有找到帮助"])
    #     return "\n".join(helps)

    # def get_helps(self, state: str):
    #     helps = self._help.get(state)
    #     if not helps:
    #         return []
    #     return [f"[{state}]"] + helps

    # @property
    # def help(self):
    #     '''获取当前状态下的帮助，没有找到则返回介绍'''
    #     if self.group.running_app_name == self.name:
    #         helps = []
    #         state = self.state
    #         helps.extend(self.get_helps(state))

    #         while "." in state:
    #             state = state.rsplit(".", 1)[0]
    #             helps.extend(self.get_helps(state))

    #         helps.extend(self.get_helps("*"))

    #         if helps:
    #             return "\n".join(helps)

    #     return self.intro

    # @property
    # def all_help(self):
    #     '''获取介绍以及全部状态下的帮助'''
    #     info = self.intro
    #     for k, v in self._help.items():
    #         v = "\n".join(v)
    #         if k != INIT_STATE:
    #             info += f"\n[{k}]\n{v}"
    #     return info

    # @help.setter
    # def help(self, help: Union[str, Dict[str, str]]):
    #     '''设置帮助，若help为str，则设置为介绍，若help为dict，则设置为对应状态的帮助'''
    #     if isinstance(help, dict):
    #         help = {k: [v.strip()] for k, v in help.items()}
    #         self._help.update(help)
    #     else:
    #         self._help[INIT_STATE] = [help.strip()]

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
        return self.group.cache_dict.get(self.name)

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

    @property
    def state(self):
        return self.group.state

    def get_state(self, *keys: str, from_: Literal["current", "plugin", "root"] = "plugin"):
        '''
            假设当前状态为 root.test.a

            - 基于 当前状态

            >>> get_state(key1, key2, from_="current") -> [root.test.a].key1.key2

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

    def _ensure_state(self, state: Union[AyakaState, str, List[str]]):
        if isinstance(state, str):
            state = self.get_state(state, from_="plugin")
        if isinstance(state, list):
            state = self.get_state(*state, from_="plugin")
        return state

    async def goto(self, state: Union[AyakaState, str, List[str]]):
        state = self._ensure_state(state)
        return await self.group.goto(state)

    async def back(self):
        return await self.group.back()

    def _on(self, func):
        states: List[AyakaState] = func.states
        cmds: List[str] = func.cmds
        deep: int = func.deep
        block: bool = func.bool
        for s in states:
            s.on_cmd(cmds, self.name, deep, block)(func)

    def on_state(self, *states: Union[AyakaState, str, List[str]]):
        states = [self._ensure_state(s) for s in states]

        def decorator(func):
            func.states = states
            if hasattr(func, "cmds"):
                self._on(func)
            return func
        return decorator

    def on_cmd(self, cmds: List[str], deep: Union[int, Literal["any"]] = 0, block=True):
        def decorator(func):
            func.cmds = cmds
            func.deep = deep
            func.block = block
            if hasattr(func, "states"):
                self._on(func)
            return func
        return decorator

    def on_text(self, deep: Union[int, Literal["any"]] = 0, block=True):
        return self.on_cmd([], deep, block)

    def set_start_cmds(self, *cmds: str):
        '''设置应用启动命令'''
        root_state.on_cmd(cmds, self.name)(self.start)

    async def start(self):
        '''*timer触发时不可用*

        启动应用，并发送提示'''
        await self.goto(root_state[self.name])
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

    def t_check(self, bot_id: int, group_id: int):
        # 未连接
        bot = get_bot(bot_id)
        if not bot:
            logger.warning(f"BOT({bot_id}) 未连接")
            return

        # 已禁用
        group = get_group(bot_id, group_id)
        app = group.get_app(self.name)
        if not app:
            logger.warning(f"群聊({group_id}) 已禁用 {self.name}")
            return

        return bot

    async def t_send(self, bot_id: int, group_id: int, message):
        '''timer触发回调时，想要发送消息必须使用该方法，一些上下文亦无法使用'''
        bot = self.t_check(bot_id, group_id)
        if not bot:
            return

        await bot.send_group_msg(group_id=group_id, message=message)

    async def t_send_many(self, bot_id: int, group_id: int, messages):
        '''timer触发回调时，想要发送消息必须使用该方法，一些上下文亦无法使用'''
        bot = self.t_check(bot_id, group_id)
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


on_message(priority=20, block=False, handlers=[deal_event])
