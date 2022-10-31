'''对nonebot的接受数据进行采样'''
import json
import datetime
from pathlib import Path
from nonebot.adapters.onebot.v11.adapter import Adapter


# 采样nonebot
def open_sample():
    # 保存地址
    now = datetime.datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H-%M-%S")
    path = Path("sample", date, f"{time}.jsonc")
    if not path.parent.exists():
        path.parent.mkdir(parents=True)

    with path.open("a+", encoding="utf8") as f:
        f.write("[\n// 需要格式化时，请将本文件的最后一个逗号替换为]\n")

    # money patch
    # nonebot的接收
    recv = Adapter.json_to_event
    Adapter._old_json_to_event = recv

    @classmethod
    def json_to_event(cls, json_data: dict, self_id=None):
        # 过滤心跳事件
        meta_event_type = json_data.get("meta_event_type")
        if meta_event_type == "heartbeat":
            return recv(json_data, self_id)

        # 读取时间
        now = datetime.datetime.now()
        time = now.strftime("%H:%M:%S")

        # 保存
        with path.open("a+", encoding="utf8") as f:
            f.write(f"// recv - {time}\n")
            json.dump(json_data, f, ensure_ascii=False)
            f.write(",\n\n")
        return recv(json_data, self_id)

    Adapter.json_to_event = json_to_event

    # money patch
    # nonebot的发送
    send = Adapter._call_api
    Adapter._old__call_api = send

    async def _call_api(self, bot, api, **data):
        json_data = {
            "bot_id": int(bot.self_id),
            "api": api,
            "data": data
        }

        # 读取时间
        now = datetime.datetime.now()
        time = now.strftime("%H:%M:%S")

        # 保存
        with path.open("a+", encoding="utf8") as f:
            f.write(f"// send - {time}\n")
            json.dump(json_data, f, ensure_ascii=False, default=str)
            f.write(",\n\n")
        return await send(self, bot, api, **data)

    Adapter._call_api = _call_api


# 关闭采样nonebot
def close_sample():
    # nonebot的接收
    Adapter.json_to_event = Adapter._old_json_to_event
    # nonebot的发送
    Adapter._call_api = Adapter._old__call_api
