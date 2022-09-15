from itertools import chain
import shlex
from html import unescape
from typing import List
from ..adapter import Bot, MessageEvent, GroupMessageEvent, Message, on_event
from .model import AyakaDevice, AyakaTrigger
from .bot import ayaka

# 看个人喜好
cmd_prefix = "#"


@on_event(MessageEvent)
async def deal_bot(bot: Bot, event: MessageEvent):
    abot = ayaka.get_abot(bot.self_id)

    device_id = event.user_id
    if isinstance(event, GroupMessageEvent):
        device_id = event.group_id
    device = await abot.get_device(device_id)

    # 处理
    await deal_device(device, event)

    # 抄送给监听者
    for dev in device.listeners:
        await deal_device(dev, event)


async def deal_device(device: AyakaDevice, event: MessageEvent):
    # 提取所有可用app的triggers
    apps = [app for app in device.apps if app.valid]
    triggers = list(chain.from_iterable(app.triggers for app in apps))

    # 剥离super
    super_triggers = [t for t in triggers if t.super]

    # 超级应用
    if await deal_triggers(event, super_triggers):
        return

    # 状态应用
    app = device.running_app
    if app:
        state_triggers = [t for t in app.triggers if t.state == app.state]
        await deal_triggers(event, state_triggers)
        return

    # 剥离desktop
    desktop_triggers = [t for t in triggers if not t.super and not t.state]

    # 桌面应用
    await deal_triggers(event, desktop_triggers)


async def deal_triggers(event: MessageEvent, triggers: List[AyakaTrigger]):
    # 命令
    ts = [t for t in triggers if t.cmd]
    t, msg, args = check_cmd(ts, event)
    if t:
        t.app.event = event
        t.app.message = msg
        t.app.cmd = t.cmd
        t.app.args = args
        await t.run()
        return True

    # 消息
    ts = [t for t in triggers if not t.cmd]
    for t in ts:
        t.app.event = event
        t.app.message = msg
        t.app.args = args
        await t.run()


def get_args(msg: Message):
    args: List[str] = []
    for m in msg:
        if m.is_text():
            items = shlex.split(unescape(str(m)))
            args.extend(item for item in items if item)
        else:
            args.append(unescape(str(m)))
    return args


def check_cmd(ts: List[AyakaTrigger], event: MessageEvent):
    ts.sort(key=lambda t: len(t.cmd), reverse=True)

    msg = event.message.copy()
    m = msg[0]

    if m.is_text():
        m_s = unescape(str(m))
        for t in ts:
            cmd = cmd_prefix + t.cmd
            if m_s.startswith(cmd):
                msg[0].data["text"] = m_s[len(cmd):]
                return t, msg, get_args(msg)

    return None, msg, get_args(msg)
