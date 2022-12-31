import json
import asyncio
from time import time
from typing import Callable, Coroutine
from websockets.legacy.client import Connect
from loguru import logger
from nonebot import get_driver
from .constant import AYAKA_LOGGER_NAME, bot_id, private_temp, group_temp
from .utils import divide, shorten

driver = get_driver()
logger.level(AYAKA_LOGGER_NAME, no=27, icon="⚡", color="<blue>")
port = driver.config.port
addr = f"ws://127.0.0.1:{port}/onebot/v11/ws"
logger.add(open("error.log", "a+", encoding="utf8"), level="ERROR")


class FakeQQ:
    terminal_cmds = {}
    cqhttp_acts = {}
    helps = [
        "============================",
        f"FAKE CQHTTP | UID:{bot_id}",
        "============================"
    ]

    def print(self, *args):
        '''打印到终端上'''
        text = shorten(args)
        try:
            logger.opt(colors=True).log(AYAKA_LOGGER_NAME, text)
        except:
            logger.log(AYAKA_LOGGER_NAME, text)

    def print_help(self):
        lines = [
            *self.helps,
            "CQ码：https://docs.go-cqhttp.org/cqcode",
            "ayaka_test：https://bridgel.github.io/ayaka_doc/latest/intro/test/"
        ]
        for line in lines:
            self.print(line)

    async def connect(self):
        self.print("启动测试环境中...")

        # 连接
        self.conn = Connect(
            addr,
            extra_headers={"x-self-id": bot_id}
        )
        self.ws = await self.conn.__aenter__()
        self.print_help()

        # 启动收发循环
        asyncio.create_task(self.terminal_loop())
        asyncio.create_task(self.nonebot_loop())

    async def disconnect(self):
        await self.ws.close()

    def on_terminal(self, *cmds: str):
        '''注册终端命令回调'''
        def decorator(func: Callable[[str], Coroutine]):
            cmd_str = "/".join(cmds)
            doc = func.__doc__ if func.__doc__ else func.__name__
            self.helps.append(f"{cmd_str} | {doc}")
            for cmd in cmds:
                self.terminal_cmds[cmd] = func
            return func
        return decorator

    def on_cqhttp(self, *actions: str):
        '''注册cqhttp行为回调'''
        def decorator(func: Callable[[int, dict], Coroutine]):
            for action in actions:
                self.cqhttp_acts[action] = func
            return func
        return decorator

    async def terminal_loop(self):
        '''通过终端向nonebot发消息'''
        loop = asyncio.get_event_loop()
        while True:
            line = await loop.run_in_executor(None, input)
            await self.deal_line(line)

    async def nonebot_loop(self):
        '''处理nonebot调用的api'''
        while True:
            text = await self.ws.recv()
            data = json.loads(text)

            # 调用回调
            action = data["action"]
            self.print(f"<y>{action}</y>")
            func = self.cqhttp_acts.get(action)
            if not func:
                self.print("未定义的假cqhttp动作", data)
            else:
                await func(data["echo"], data["params"])

    async def deal_line(self, line: str):
        '''处理命令行，调用对应的函数'''
        line = line.strip()
        if not line:
            return

        # 拆解命令和参数
        cmd, text = divide(line)

        # 调用回调
        func = self.terminal_cmds.get(cmd)
        if not func:
            self.print("未知终端命令", cmd, text)
        else:
            await func(text)

    async def send_echo(self, echo: int, data):
        '''向nonebot发送假应答消息'''
        data = {
            'data': data,
            'echo': echo,
            'retcode': 0,
            'status': 'ok'
        }
        await self.ws.send(json.dumps(data))

    async def send_group(self, gid: int, uid: int, text: str):
        '''向nonebot发送假群聊消息'''
        data = group_temp
        name = f"测试{uid}号"
        data["message"] = data["raw_message"] = text
        data["sender"]["user_id"] = data["user_id"] = uid
        data["sender"]["card"] = data["sender"]["nickname"] = name
        data["time"] = int(time())
        data["group_id"] = gid
        # 发送假cqhttp消息
        await self.ws.send(json.dumps(data))
        # 回显
        self.print(f"群聊({gid}) <y>{name}</y>({uid}) 说：\n{text}")

    async def send_private(self, uid: int, text: str):
        '''向nonebot发送假私聊消息'''
        data = private_temp
        name = f"测试{uid}号"
        data["message"] = data["raw_message"] = text
        data["sender"]["user_id"] = data["user_id"] = uid
        data["sender"]["nickname"] = name
        data["time"] = int(time())
        # 发送假cqhttp消息
        await self.ws.send(json.dumps(data))
        # 回显
        self.print(f"私聊({uid}) <y>{name}</y> 说：\n{text}")


fake_qq = FakeQQ()


@driver.on_startup
async def _():
    asyncio.create_task(fake_qq.connect())


@driver.on_shutdown
async def _():
    await fake_qq.disconnect()
