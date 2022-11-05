from contextvars import ContextVar
from collections import defaultdict
from typing import List, TYPE_CHECKING, Dict
from .driver import Message, MessageSegment, Bot, MessageEvent
from .cache import AyakaCacheCtrl

if TYPE_CHECKING:
    from .ayaka import AyakaApp
    from .group import AyakaGroup


_bot: ContextVar[Bot] = ContextVar("_bot")
_event: ContextVar[MessageEvent] = ContextVar("_event")
_group: ContextVar["AyakaGroup"] = ContextVar("_group")
_arg: ContextVar[Message] = ContextVar("_arg")
_args: ContextVar[List[MessageSegment]] = ContextVar("_args")
_message: ContextVar[Message] = ContextVar("_message")
_cmd: ContextVar[str] = ContextVar("_cmd")

app_list: List["AyakaApp"] = []
group_list: List["AyakaGroup"] = []
bot_list: List[Bot] = []

# 监听私聊
private_listener_dict: Dict[int, List[int]] = defaultdict(list)
