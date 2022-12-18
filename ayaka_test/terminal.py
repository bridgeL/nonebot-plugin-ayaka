import asyncio
from pathlib import Path

from .utils import record
from .core import fake_qq, divide
from .sample import open_sample, close_sample


@fake_qq.on_terminal("d")
async def delay(text: str):
    '''延时x秒'''
    try:
        n = float(text.strip())
    except:
        n = 1
    await asyncio.sleep(n)


@fake_qq.on_terminal("dn")
async def _(text: str):
    '''延时x秒后空一行'''
    await delay(text)
    print()


@fake_qq.on_terminal("g")
async def _(text: str):
    '''<group_id> <user_id> <text> | 发送群聊消息'''
    items = text.split(" ", maxsplit=2)
    if len(items) == 3:
        record(f"\"user\" 说：{items[2]}")
        await fake_qq.send_group(*items)


@fake_qq.on_terminal("p")
async def dd_(text: str):
    '''<user_id> <text> | 发送私聊消息'''
    items = text.split(" ", maxsplit=1)
    if len(items) == 2:
        await fake_qq.send_private(*items)


@fake_qq.on_terminal("s")
async def _(text: str):
    '''<name> | 执行 script/<name>.ini自动化脚本'''
    # 脚本名称
    script_name = text
    path = Path("script", script_name)

    path = path.with_suffix(".ini")
    if not path.is_file():
        fake_qq.print("脚本不存在")
        return

    with path.open("r", encoding="utf8") as f:
        data = f.read()

    # 拆分成行
    lines = data.split("\n")

    temp = []
    for line in lines:
        # 去除首尾空格
        line = line.strip()

        # 排除注释和空
        if not line or line.startswith((";", "#")):
            continue

        temp.append(line)

    lines = temp

    # 执行脚本
    before = ""
    after = "dn 0.2"
    for line in lines:
        cmd, text = divide(line)
        if cmd == "after":
            after = text
            continue

        if cmd == "before":
            before = text
            continue

        if before:
            await fake_qq.deal_line(before)

        await fake_qq.deal_line(line)

        if after:
            await fake_qq.deal_line(after)


@fake_qq.on_terminal("h")
async def _(text: str):
    '''帮助'''
    fake_qq.print_help()


@fake_qq.on_terminal("sa")
async def _(text: str):
    '''on/off | 打开/关闭nonebot采样'''
    if text == "on":
        open_sample()
        fake_qq.print("已打开cqhttp采样")
    else:
        close_sample()
        fake_qq.print("已关闭cqhttp采样")
