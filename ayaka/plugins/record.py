from html import unescape
import time
from pathlib import Path

from .. import *


def safe_log(ss):
    s = ss[:1000]
    if len(ss) > 1000:
        s += "..."

    try:
        logger.success(s)
    except:
        logger.opt(colors=False).success(s)


@on_event(MessageEvent, priority=1)
async def record_recv(bot: Bot, event: MessageEvent):
    safe_log(unescape(str(event)))

    name = event.sender.nickname
    device_id = event.user_id
    if isinstance(event, GroupMessageEvent):
        if event.sender.card:
            name = event.sender.card
        device_id = event.group_id

    record(bot.self_id, device_id, event.time, name,
           event.user_id, unescape(str(event.message)))


@on_send
async def record_send(bot: Bot, api: str, data: dict):
    safe_log(str(data))

    device_id = data['group_id'] if 'group_id' in data else data['user_id']
    if api == "send_group_forward_msg":
        data = data["messages"]
        for d in data:
            msg = unescape(str(d["data"]["content"]))
            record(bot.self_id, device_id, int(
                time.time()), "AyakaBot", bot.self_id, msg)
    else:
        data = data["message"]
        record(bot.self_id, device_id, int(time.time()),
               "AyakaBot", bot.self_id, str(data))


def record(bot_id: str, device_id: int, time_i: int, name: str, uid: int, msg: str):
    file_name = time.strftime("%Y-%m-%d", time.localtime()) + ".log"
    path = Path("data", "record", bot_id, str(device_id), file_name)
    if not path.parent.exists():
        path.parent.mkdir(parents=True)

    line = f"[{time_i}] {name}({uid}) 说: {msg}\n"
    with path.open("a+", encoding="utf8") as f:
        f.write(line)
