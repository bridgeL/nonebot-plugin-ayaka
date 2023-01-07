'''存放一些让人抓狂的money patch方法'''
import json
import datetime
from nonebot.drivers.fastapi import FastAPIWebSocket
from nonebot.adapters.onebot.v11.adapter import Adapter
from .helpers import Timer, safe_open_file


def hack_load_plugin():
    '''nonebot.plugin.manager PluginManager.load_plugin方法

    令nb导入插件时，统计导入时长'''
    from nonebot.plugin.manager import PluginManager
    origin_func = PluginManager.load_plugin

    def func(self, name):
        with Timer(name):
            return origin_func(self, name)

    PluginManager.load_plugin = func


class Recorder:
    '''记录nb和gocq的对话'''

    def __init__(self) -> None:
        self.data = {}
        now = datetime.datetime.now()
        date = now.strftime("%Y-%m-%d")
        time = now.strftime("%H-%M-%S")
        self.base = f"data/sample/{date}/{time}"

    def record_send(self, data: dict):
        '''记录nb发送数据'''
        if "echo" not in data:
            return

        print("send", data)

        echo = data["echo"]
        self.data[echo] = data

    def record_recv(self, data: dict):
        '''记录nb接收数据'''
        if "echo" not in data:
            return

        print("recv", data)

        echo = data["echo"]
        _data = self.data.pop(echo, None)
        if _data:
            data = [_data, data]
            with safe_open_file(f"{self.base}/{echo}.json") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)


recorder = Recorder()


class WatcherWebSocket(FastAPIWebSocket):
    '''受监督的FastAPI ws'''

    async def receive(self) -> str | bytes:
        data = await super().receive()
        if isinstance(data, str):
            recorder.record_recv(json.loads(data))
        return data

    async def send_text(self, data: str) -> None:
        recorder.record_send(json.loads(data))
        return await super().send_text(data)


class WatcherAdapter(Adapter):
    '''受监督的Onebot适配器'''
    async def _handle_ws(self, websocket: FastAPIWebSocket) -> None:
        ws = WatcherWebSocket(
            request=websocket.request,
            websocket=websocket.websocket
        )
        return await super()._handle_ws(ws)
