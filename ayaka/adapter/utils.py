from math import ceil
from typing import Callable, Awaitable, List
from nonebot import logger as base_logger
from nonebot import get_driver, on
from nonebot.rule import Rule
from nonebot.adapters.onebot.v11 import Event, escape
from nonebot.adapters.onebot.v11 import Bot as BaseBot


class Bot(BaseBot):
    async def send_group_forward_msg(
        self,
        group_id: int,
        messages: List[str],
    ) -> None:
        # 自动分割长消息组（不可超过100条）
        n = 80
        for i in range(ceil(len(messages) / n)):
            # 自动转换为cqhttp node格式
            nodes = self.pack_message_nodes(messages[i*n: (i+1)*n])
            await self.call_api("send_group_forward_msg", group_id=group_id, messages=nodes)

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
                    "uin": self.self_id,
                    "content": escape(str(m), escape_comma=False)
                }
            })
        return nodes


driver = get_driver()
logger = base_logger.opt(colors=True)


def on_connect(func: Callable[[Bot], Awaitable]):
    async def _func(bot: BaseBot):
        await func(Bot(bot.adapter, bot.self_id))
    driver.on_bot_connect(_func)


def on_event(cls, priority=5):
    def decorator(func: Callable[[Bot, Event], Awaitable]):
        async def checker(event: Event):
            if isinstance(event, cls):
                return True
        async def _func(bot: BaseBot, event:Event):
            await func(Bot(bot.adapter, bot.self_id), event)
        on(rule=Rule(checker), priority=priority, block=False).handle()(_func)

    return decorator


def on_send(func: Callable[[Bot, str, dict], Awaitable]):
    async def _func(bot: Bot, api: str, data: dict):
        if api not in ["send_msg", "send_group_msg", "send_private_msg", "send_group_forward_msg"]:
            return
        await func(Bot(bot.adapter, bot.self_id), api, data)

    Bot.on_calling_api(_func)
