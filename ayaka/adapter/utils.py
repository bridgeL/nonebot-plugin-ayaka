from typing import Callable, Awaitable
from nonebot import logger as base_logger
from nonebot import get_driver, on
from nonebot.rule import Rule
from nonebot.adapters.onebot.v11 import Bot, Event

driver = get_driver()
logger = base_logger.opt(colors=True)


def on_connect(func: Callable[[Bot], Awaitable]):
    driver.on_bot_connect(func)


def on_event(cls, priority=5):
    def decorator(func: Callable[[Bot, Event], Awaitable]):
        async def checker(event: Event):
            if isinstance(event, cls):
                return True

        rule = Rule(checker)
        on(rule=rule, priority=priority, block=False).handle()(func)

    return decorator


def on_send(func: Callable[[Bot, str, dict], Awaitable]):
    async def _func(bot: Bot, api: str, data: dict):
        if api not in ["send_msg", "send_group_msg", "send_private_msg"]:
            return
        await func(bot, api, data)

    Bot.on_calling_api(_func)
