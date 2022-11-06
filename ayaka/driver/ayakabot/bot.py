import json
from typing import Any, Callable, Awaitable, List, Union
from functools import partial
from typing_extensions import Protocol

# from .utils import safe_cqhttp_utf8
from .result import ResultStore
from .event import Event
from .websocket import FastAPIWebSocket
from .message import Message, MessageSegment
from .model import DataclassEncoder

from ayaka.logger import logger


class _ApiCall(Protocol):
    async def __call__(self, **kwargs: Any) -> Any:
        ...


class Bot:
    """
    OneBot v11 协议 Bot 适配。
    """

    _calls: List[Callable[["Bot", str, dict], Awaitable]] = []

    def __init__(self, ws: FastAPIWebSocket, self_id: str):
        self.ws = ws
        self.self_id = self_id

    def __getattr__(self, name: str) -> _ApiCall:
        return partial(self.call_api, name)

    @classmethod
    def on_call(self, func: Callable[["Bot", str, dict], Awaitable]):
        self._calls.append(func)

    async def call_api(self, api: str, **data) -> Any:
        """
        :说明:

          调用 OneBot 协议 API
        """
        logger.opt(colors=True).debug(f"Calling API <y>{api}</y>")

        websocket = self.ws
        if not websocket:
            logger.warning("没有建立ws连接，无法发送消息")
            return

        # 调用钩子
        for call in self._calls:
            await call(self, api, data)

        # # 解决cqhttp莫名其妙被风控的问题
        # data = safe_cqhttp_utf8(api, data)

        # 生成 seq码 和 待发送的json数据
        seq = ResultStore.get_seq()
        json_data = json.dumps(
            {"action": api, "params": data, "echo": {"seq": seq}},
            cls=DataclassEncoder,
        )

        try:
            await websocket.send(json_data)
            # 默认30s超时
            result = await ResultStore.fetch(seq, 30)
            if isinstance(result, dict):
                if result.get("status") == "failed":
                    raise
                return result.get("data")

        except:
            logger.exception("发送消息失败")

    async def send(
        self,
        event: Event,
        message: Union[str, Message, MessageSegment],
        **kwargs,
    ) -> Any:
        """
        :说明:

          根据 ``event``  向触发事件的主体发送消息。
        """

        # 生成Message
        if isinstance(message, Message):
            msg = message
        else:
            msg = Message(message)

        params = {}

        # 填写目标id
        if getattr(event, "user_id", None):
            params["user_id"] = getattr(event, "user_id")
        if getattr(event, "group_id", None):
            params["group_id"] = getattr(event, "group_id")

        # 加载其他信息
        params.update(kwargs)

        # 填写群聊/私聊
        if "message_type" not in params:
            if params.get("group_id", None):
                params["message_type"] = "group"
            elif params.get("user_id", None):
                params["message_type"] = "private"
            else:
                raise ValueError("Cannot guess message type to reply!")

        params["message"] = msg

        return await self.call_api("send_msg", **params)
