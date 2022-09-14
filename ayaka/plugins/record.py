from html import unescape
import time
from pathlib import Path

from .. import *


def get_desc(event, limit: int = 0):
    s = unescape(str(event))
    if limit > 0:
        if len(s) > limit:
            s = s[:limit] + "..."
    return s


@on_event(MessageEvent, priority=1)
async def record_recv(bot: Bot, event: MessageEvent):
    logger.success(get_desc(event))

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
    logger.success(str(data).replace("<", "\<"))

    device_id = data['group_id'] if 'group_id' in data else data['user_id']
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
