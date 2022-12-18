'''所有上下文变量'''
from contextvars import ContextVar
from collections import defaultdict
from re import Match
from typing import List, TYPE_CHECKING, Dict
from .driver import Message, MessageSegment, Bot, MessageEvent, get_driver
from .utils import singleton

if TYPE_CHECKING:
    from .ayaka import AyakaApp, AyakaGroup


_bot: ContextVar[Bot] = ContextVar("_bot")
_event: ContextVar[MessageEvent] = ContextVar("_event")
_group: ContextVar["AyakaGroup"] = ContextVar("_group")
_arg: ContextVar[Message] = ContextVar("_arg")
_args: ContextVar[List[MessageSegment]] = ContextVar("_args")
_message: ContextVar[Message] = ContextVar("_message")
_cmd: ContextVar[str] = ContextVar("_cmd", default="")
_cmd_regex: ContextVar[Match] = ContextVar("_cmd_regex", default=None)

app_list: List["AyakaApp"] = []
group_list: List["AyakaGroup"] = []
bot_list: List[Bot] = []

# 监听私聊
private_listener_dict: Dict[int, List[int]] = defaultdict(list)


driver = get_driver()


@singleton
def start_timers():
    '''开启插件中的定时模块，仅执行一次'''
    for app in app_list:
        for t in app.timers:
            t.start()


@driver.on_bot_connect
async def bot_connect(bot: Bot):
    bot_list.append(bot)
    start_timers()


@driver.on_bot_disconnect
async def bot_disconnect(bot: Bot):
    bot_list.remove(bot)
