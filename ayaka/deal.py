
import shlex
from html import unescape
from typing import List
from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GroupMessageEvent, Message
from .model import AyakaDevice, AyakaApp, Trigger
from .bot import ayaka_bots

# 看个人喜好
cmd_prefix = "#"

matcher = on_message(priority=1)


@matcher.handle()
async def deal(bot: Bot, event: MessageEvent):
    device_id = event.user_id
    if isinstance(event, GroupMessageEvent):
        device_id = event.group_id

    abot = ayaka_bots[bot.self_id]
    device = await abot.get_device(device_id)
    if not device:
        raise

    # 处理
    await deal_device(device, event)

    # 抄送给监听者
    for device_id in device.listeners:
        dev = await abot.get_device(device_id)
        await deal_device(dev, event)


async def deal_device(device: AyakaDevice, event: MessageEvent):
    # 剥离super和desktop
    super_triggers: List[Trigger] = []
    desktop_triggers: List[Trigger] = []
    apps = [app for app in device.apps.values() if app.valid]
    for app in apps:
        super_triggers.extend(app.super_triggers)
        desktop_triggers.extend(app.desktop_triggers)

    # 超级应用
    if await deal_triggers(event, super_triggers, device=device):
        return

    # 状态应用
    name = device.running_app_name
    if name:
        app = device.apps[name]
        ts = [t for t in app.state_triggers if t.state == app.state]
        await deal_triggers(event, ts, app=app)
        return

    # 桌面应用
    await deal_triggers(event, desktop_triggers, device=device)


async def deal_triggers(event: MessageEvent, triggers: List[Trigger], device: AyakaDevice = None, app: AyakaApp = None):
    # 命令
    ts = [t for t in triggers if t.cmd]
    t, msg, args = check_cmd(ts, event)
    if t:
        await run_trigger(event, t, msg, args, device, app)
        return True

    # 消息
    ts = [t for t in triggers if not t.cmd]
    for t in ts:
        await run_trigger(event, t, msg, args, device, app)


async def run_trigger(event: MessageEvent, t: Trigger, msg, args: List[str], device: AyakaDevice = None, app: AyakaApp = None):
    if not app:
        app = device.apps[t.app_name]

    app.event = event
    app.message = msg
    app.cmd = t.cmd
    app.args = args

    # 上 下 文 切 换
    app.module.app = app
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


def check_cmd(ts: List[Trigger], event: MessageEvent):
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
