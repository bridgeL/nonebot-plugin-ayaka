from importlib import import_module
import json
import asyncio
import uvicorn
from loguru import logger
from fastapi import FastAPI, WebSocket
from pathlib import Path
import re

from .bot import Bot
from .event import json_to_event, MessageEvent
from .websocket import FastAPIWebSocket
from ...config import ayaka_root_config

app = FastAPI()


class Config:
    port = ayaka_root_config.ayaka_port
    ayaka_prefix = "#"
    ayaka_separate = " "
    ayaka_exclude_old = True
    fastapi_reload = True


class Driver:
    connect_calls = []
    disconnect_calls = []
    deal_event = None
    config = Config()

    def deal(self, bot, event):
        if self.deal_event:
            if isinstance(event, MessageEvent):
                logger.success(str(event))
                asyncio.create_task(self.deal_event(bot, event))

    async def bot_connect(self, bot: Bot):
        ts = []
        for call in self.connect_calls:
            ts.append(asyncio.create_task(call(bot)))
        await asyncio.gather(*ts)

    async def bot_disconnect(self, bot: Bot):
        ts = []
        for call in self.disconnect_calls:
            ts.append(asyncio.create_task(call(bot)))
        await asyncio.gather(*ts)

    def on_bot_connect(self, func):
        self.connect_calls.append(func)

    def on_bot_disconnect(self, func):
        self.disconnect_calls.append(func)

    def on_startup(self, func):
        app.on_event("startup")(func)

    def on_shutdown(self, func):
        app.on_event("shutdown")(func)


driver = Driver()


# 启动服务
def run(host="127.0.0.1", port=driver.config.port, reload=True):
    tip = f'''
您目前正在使用AYAKA BOT！
注意设置cqhttp连接配置为
- 反向ws
- ws://127.0.0.1:{port}/onebot/v11/ws
'''
    print(tip)
    uvicorn.run(
        app=f"{__name__}:app",
        host=host,
        port=port,
        reload=reload,
    )


def load_plugins(path):
    path = Path(path)
    for p in path.iterdir():
        if p.name.startswith("_"):
            continue

        load_plugin(p)


def load_plugin(path):
    if isinstance(path, Path):
        p = path
    else:
        p = Path(path)

    name = re.sub(r"\\|/", ".", str(p))
    name = re.sub(r".py$", "", name)
    try:
        import_module(name)
        logger.opt(colors=True).success(f"导入成功 \"<y>{p.stem}</y>\"")
    except:
        logger.opt(colors=True).exception(f"导入失败 \"<y>{p.stem}</y>\"")


@app.websocket("/onebot/v11/ws")
async def endpoint(websocket: WebSocket):
    self_id = websocket.headers.get("x-self-id")
    ws = FastAPIWebSocket(websocket)
    bot = Bot(ws, self_id)

    # 建立ws连接
    await ws.accept()
    await driver.bot_connect(bot)

    try:
        # 监听循环
        while True:
            data = await ws.receive()
            json_data = json.loads(data)
            # 将json解析为对应的event
            event = json_to_event(json_data)

            if not event:
                continue

            driver.deal(bot, event)

    except:
        logger.exception("连接中断")
    finally:
        # 结束ws连接
        await driver.bot_disconnect(bot)
        await ws.close()


def get_driver():
    return driver


def on_message(priority, block, handlers):
    driver.deal_event = handlers[0]
