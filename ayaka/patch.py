'''存放一些让人抓狂的money patch方法'''
import json
import datetime
from nonebot.drivers.fastapi import FastAPIWebSocket
from nonebot.adapters.onebot.v11.adapter import Adapter
from .helpers import Timer, ensure_dir_exists, logger


def hack_on_shutdown():
    '''money patch nonebot.internal.driver.Driver.on_shutdown

    查看都是谁shutdown那么慢'''
    from nonebot import get_driver
    driver = get_driver()
    origin_func = driver.on_shutdown

    def _func(func):
        async def __func():
            print(f"[{func.__module__} {func.__name__}]")
            t = Timer(show=False)
            with t:
                await func()
            print(f"耗时{t.diff:.2f}s")
        return origin_func(__func)

    driver.on_shutdown = _func


def hack_load_plugin():
    '''money patch nonebot.plugin.manager PluginManager.load_plugin

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
        self.show_data = True

    def record_send(self, data: dict):
        '''记录nb发送数据'''
        if "echo" not in data:
            return

        if self.show_data:
            print(data)

        echo = data["echo"]
        self.data[echo] = data

    def record_recv(self, data: dict):
        '''记录nb接收数据'''
        if "echo" not in data:
            return

        if self.show_data:
            print(data)

        echo = data["echo"]
        _data = self.data.pop(echo, None)
        if not _data:
            return

        data = [_data, data]
        path = ensure_dir_exists(f"{self.base}/{echo}.json")
        with path.open("a+", encoding="utf8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)


recorder = Recorder()


def dont_show_record():
    '''设置监督内容不回显'''
    recorder.show_data = False


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

    def __init__(self, driver, **kwargs):
        logger.warning("正在使用受监督的Onebot适配器，将产生大量data/sample/xx.json日志文件")
        super().__init__(driver, **kwargs)

    async def _handle_ws(self, websocket: FastAPIWebSocket) -> None:
        ws = WatcherWebSocket(
            request=websocket.request,
            websocket=websocket.websocket
        )
        return await super()._handle_ws(ws)
