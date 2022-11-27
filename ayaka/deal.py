import asyncio
import datetime
from typing import List

from .driver import Message, MessageSegment, Bot, MessageEvent, GroupMessageEvent
from .on import AyakaTrigger
from .config import sep, prefix, exclude_old
from .constant import _bot, _event, _group, _arg, _args, _message, _cmd, private_listener_dict
from .group import get_group


async def deal_event(bot: Bot, event: MessageEvent):
    if exclude_old:
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
    # 群组
    group = get_group(bot_id, group_id)
    _group.set(group)

    # 消息
    message = _event.get().message
    _message.set(message)

    # 命令、参数
    cmd = get_cmd(message)
    _cmd.set(cmd)

    # 让super先来
    triggers = []
    for app in group.apps:
        for t in app.super_triggers:
            triggers.append(t)

    # 若执行了super命令，则退出
    if await deal_triggers(triggers):
        return

    # 普通命令继续
    triggers = []

    # 当前正在运行
    app = group.running_app
    if app:
        for t in app.state_triggers:
            if t.state == "*":
                triggers.append(t)
            else:
                # 子状态
                # s1 = 添加.
                # s2 = 添加.姓名.
                s1 = t.state + "."
                s2 = app.state + "."
                if s2.startswith(s1):
                    triggers.append(t)

    # 其他桌面应用
    else:
        for app in group.apps:
            for t in app.no_state_triggers:
                triggers.append(t)

    await deal_triggers(triggers)


async def deal_triggers(triggers: List[AyakaTrigger]):
    triggers.sort(key=lambda t: str(t.state), reverse=True)

    cmd = _cmd.get()
    msg = _message.get()

    # 命令
    if cmd:
        for t in triggers:
            if t.cmd == cmd:
                # 设置去掉命令后的消息
                arg = remove_cmd(cmd, msg)
                _arg.set(arg)
                _args.set(divide_message(arg))
                await t.run()
                return True

    _arg.set(msg)
    _args.set(divide_message(msg))

    # 命令退化成消息
    for t in triggers:
        if not t.cmd:
            await t.run()


def get_cmd(message: Message):
    '''返回命令'''
    first = ""
    for m in message:
        if m.type == "text":
            first += str(m)
        else:
            break
    if not first or not first.startswith(prefix):
        return ""
    first += sep
    return first.split(sep, 1)[0][len(prefix):]


def divide_message(message: Message):
    args: List[MessageSegment] = []

    for m in message:
        if m.is_text():
            ss = str(m).split(sep)
            args.extend(MessageSegment.text(s) for s in ss if s)
        else:
            args.append(m)

    return args


def remove_cmd(cmd: str, message: Message):
    m = message[0]
    if m.is_text():
        m_str = str(m)
        m_str = m_str[len(prefix+cmd):].lstrip(sep)
        if not m_str:
            return message[1:]
        return [MessageSegment.text(m_str)] + message[1:]
    return message
