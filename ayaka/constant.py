'''所有上下文变量'''
from contextvars import ContextVar
from collections import defaultdict
from typing import List, TYPE_CHECKING, Dict
from .driver import Message, MessageSegment, Bot, MessageEvent, get_driver


if TYPE_CHECKING:
    from .ayaka import AyakaApp, AyakaGroup


_bot: ContextVar[Bot] = ContextVar("_bot")
_event: ContextVar[MessageEvent] = ContextVar("_event")
_group: ContextVar["AyakaGroup"] = ContextVar("_group")
_arg: ContextVar[Message] = ContextVar("_arg")
_args: ContextVar[List[MessageSegment]] = ContextVar("_args")
_message: ContextVar[Message] = ContextVar("_message")
_cmd: ContextVar[str] = ContextVar("_cmd")
_enter_exit_during: ContextVar[int] = ContextVar(
    "_enter_exit_during", default=0)

app_list: List["AyakaApp"] = []
group_list: List["AyakaGroup"] = []
bot_list: List[Bot] = []

# 监听私聊
private_listener_dict: Dict[int, List[int]] = defaultdict(list)


first_bot_connect = True
driver = get_driver()


@driver.on_bot_connect
async def bot_connect(bot: Bot):
    bot_list.append(bot)

    # 在第一个bot就绪后，开启插件中的定时模块
    global first_bot_connect
    if first_bot_connect:
        first_bot_connect = False
        for app in app_list:
            for t in app.timers:
                t.start()


@driver.on_bot_disconnect
async def bot_disconnect(bot: Bot):
    bot_list.remove(bot)
