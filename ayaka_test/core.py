import re
import sys
import json
import asyncio
from time import time
from typing import Callable, Coroutine
from websockets.legacy.client import Connect
from nonebot import get_driver
from ayaka import logger
from ayaka.config import AYAKA_DEBUG


AYAKA_LOGGER_NAME = "AYAKA"

driver = get_driver()
logger.level(AYAKA_LOGGER_NAME, no=26, icon="⚡", color="<blue>")


def divide(line):
    if " " not in line:
        line += " "
    cmd, text = line.split(" ", maxsplit=1)
    return cmd, text


bot_id = 123

helps = f'''
============================
FAKE CQHTTP | UID:{bot_id}

<y>h</y>                             | 帮助
<y>g</y> <group_id> <user_id> <text> | 发送群聊消息
<y>p</y> <user_id> <text>            | 发送私聊消息
<y>sa</y> on/off                     | 打开/关闭nonebot采样

<y>d</y> <float>                     | 延时x秒
<y>dn</y> <float>                    | 延时x秒后空一行

<y>s</y> [-p echo] -n 1 测试一下aa   | 执行[plugins/echo/]script/1.ini自动化脚本
<y>hide</y>                          | 关闭脚本命令回显
<y>before</y>                        | 在运行每一命令前执行命令
<y>after</y>                         | 在运行每一命令后执行命令
<y># ;</y>                           | 注释
<y>$1 $2 $3</y>                      | 脚本变量
============================
'''.strip()

private_temp = {
    "post_type": "message",
    "message_type": "private",
    "time": 0,
    "self_id": bot_id,
    "sub_type": "friend",
    "user_id": 0,
    "target_id": bot_id,
    "message": "",
    "raw_message": "",
    "font": 0,
    "sender": {
        "age": 0,
        "nickname": "",
        "sex": "unknown",
        "user_id": 0
    },
    "message_id": -1
}

group_temp = {
    "post_type": "message",
    "message_type": "group",
    "time": 0,
    "self_id": bot_id,
    "sub_type": "normal",
    "sender": {
        "age": 0,
        "area": "",
        "card": "",
        "level": "",
        "nickname": "",
        "role": "owner",
        "sex": "unknown",
        "title": "",
        "user_id": 0
    },
    "message_id": -1,
    "anonymous": None,
    "font": 0,
    "raw_message": "",
    "user_id": 0,
    "group_id": 0,
    "message": "",
    "message_seq": 0
}


class FakeQQ:
    terminal_cmds = {}
    cqhttp_acts = {}

    def print(self, *args):
        '''打印到终端上'''
        text = " ".join(str(a) for a in args)
        # 保护已闭合的标签
        text = re.sub(r"<(.*)>(.*?)</(\1)>", r"%%%\1%%%\2%%%/\1%%%", text)
        # 注释未闭合的标签
        text = re.sub(r"<.*?>", r"\\\g<0>", text)
        # 恢复已闭合的标签
        text = re.sub(r"%%%(.*)%%%(.*?)%%%/(\1)%%%", r"<\1>\2</\1>", text)
        try:
            logger.opt(colors=True).log(AYAKA_LOGGER_NAME, text)
        except:
            logger.log(AYAKA_LOGGER_NAME, text)

    def init_logger(self):
        logger.remove()
        logger.add(
            sys.stdout,
            level="DEBUG",
            format="<g>{time:HH:mm:ss}</g> | <level>{level}</level> | {message}",
            filter={
                "nonebot": "DEBUG" if AYAKA_DEBUG else "WARNING",
                "uvicorn": "INFO",
                "websockets": "WARNING"
            },
            backtrace=False,
            diagnose=False
        )

    async def connect(self):
        # 初始化
        self.init_logger()
        self.print("启动测试环境中...")

        # 连接
        port = driver.config.port
        self.conn = Connect(
            f"ws://127.0.0.1:{port}/onebot/v11/ws",
            extra_headers={"x-self-id": bot_id}
        )
        self.ws = await self.conn.__aenter__()

        self.print_help()

        # 启动收发循环
        asyncio.create_task(self.terminal_loop())
        asyncio.create_task(self.nonebot_loop())

    async def disconnect(self):
        # 断开连接
        await self.ws.close()

    def on_terminal(self, *cmds: str):
        '''注册终端命令回调'''
        def decorator(func: Callable[[str], Coroutine]):
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
            print()
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

    def print_help(self):
        for line in helps.split("\n"):
            self.print(line)
        self.print("CQ码：https://docs.go-cqhttp.org/cqcode")
        self.print("ayaka_test：https://bridgel.github.io/ayaka_doc/test/")


fake_qq = FakeQQ()


@driver.on_startup
async def _():
    asyncio.create_task(fake_qq.connect())


@driver.on_shutdown
async def _():
    await fake_qq.disconnect()
