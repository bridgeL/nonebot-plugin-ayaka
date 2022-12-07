'''处理收到的消息，将其分割为cmd和args，设置上下文相关变量的值，并将消息传递给对应的群组'''
import asyncio
import datetime
from typing import List
from loguru import logger
from pydantic import ValidationError

from .driver import Message, MessageSegment, Bot, MessageEvent, GroupMessageEvent
from .config import ayaka_root_config
from .constant import _bot, _event, _group, _arg, _args, _message, _cmd, private_listener_dict
from .group import get_group
from .state import AyakaState, AyakaTrigger


async def deal_event(bot: Bot, event: MessageEvent):
    if ayaka_root_config.exclude_old_msg:
        time_i = int(datetime.datetime.now().timestamp())
        if event.time < time_i - 60:
            return

    _bot.set(bot)
    _event.set(event)

    bot_id = int(bot.self_id)

    if isinstance(event, GroupMessageEvent):
        group_id = event.group_id
        await deal_group(bot_id, group_id)

    else:
        id = event.user_id
        group_ids = private_listener_dict.get(id, [])
        ts = [asyncio.create_task(deal_group(bot_id, group_id))
              for group_id in group_ids]
        await asyncio.gather(*ts)


async def deal_group(bot_id: int, group_id: int):
    prefix = ayaka_root_config.prefix

    # 群组
    group = get_group(bot_id, group_id)
    _group.set(group)

    # 消息
    message = _event.get().message
    _message.set(message)

    # 从子状态开始向上查找可用的触发
    state = group.state
    cascade_triggers = get_cascade_triggers(state, 0)

    # 命令
    # 消息前缀文本
    first = get_first(message)
    if first.startswith(prefix):
        first = first[len(prefix):]
        for ts in cascade_triggers:
            if await deal_cmd_triggers(ts, message, first, state):
                return

    # 命令退化成消息
    for ts in cascade_triggers:
        if await deal_text_triggers(ts, message, state):
            return


async def deal_cmd_triggers(triggers: List[AyakaTrigger], message: Message, first: str, state: AyakaState):
    sep = ayaka_root_config.separate

    # 命令
    temp = [t for t in triggers if t.cmds]
    # 根据命令长度排序，长命令优先级更高
    cmd_ts = [(c, t) for t in temp for c in t.cmds]
    cmd_ts.sort(key=lambda x: len(x[0]), reverse=1)

    for c, t in cmd_ts:
        if first.startswith(c):
            # 设置上下文
            # 设置命令
            _cmd.set(c)
            # 设置参数
            left = first[len(c):].lstrip(sep)
            if left:
                arg = Message([MessageSegment.text(left), *message[1:]])
            else:
                arg = Message(message[1:])
            _arg.set(arg)
            _args.set(divide_message(arg))

            # 触发
            log_trigger(c, t.app_name, state, t.func.__name__)
            await t.run()

            # 阻断后续
            if t.block:
                return True


async def deal_text_triggers(triggers: List[AyakaTrigger], message: Message, state: AyakaState):
    # 消息
    text_ts = [t for t in triggers if not t.cmds]

    # 设置上下文
    # 设置命令
    _cmd.set("")
    # 设置参数
    _arg.set(message)
    _args.set(divide_message(message))

    for t in text_ts:
        # 触发
        log_trigger("", t.app_name, state, t.func.__name__)
        await t.run()

        # 阻断后续
        if t.block:
            return True


def get_cascade_triggers(state: AyakaState, deep: int = 0):
    # 根据深度筛选funcs
    ts = [
        t for t in state.triggers
        if t.deep == "all" or t.deep >= deep
    ]
    cascade_triggers = [ts]

    # 获取父状态的方法
    if state.parent:
        cascade_triggers.extend(get_cascade_triggers(state.parent, deep+1))

    # 排除空项
    cascade_triggers = [ts for ts in cascade_triggers if ts]
    return cascade_triggers


def log_trigger(cmd, app_name, state, func_name):
    '''日志记录'''
    items = []
    items.append(f"状态：<c>{state}</c>")
    items.append(f"应用：<y>{app_name}</y>")
    if cmd:
        items.append(f"命令：<y>{cmd}</y>")
    else:
        items.append("命令：<g>无</g>")
    items.append(f"回调：<c>{func_name}</c>")
    info = " | ".join(items)
    logger.opt(colors=True).debug(info)


def get_first(message: Message):
    first = ""
    for m in message:
        if m.type == "text":
            first += str(m)
        else:
            break
    return first


def divide_message(message: Message) -> List[MessageSegment]:
    args = []
    sep = ayaka_root_config.separate

    for m in message:
        if m.is_text():
            ss = str(m).split(sep)
            args.extend(MessageSegment.text(s) for s in ss if s)
        else:
            args.append(m)

    return args
