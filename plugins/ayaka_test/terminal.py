import asyncio
from pathlib import Path
import re
import shlex
from .core import fake_qq, divide
from .sample import open_sample, close_sample


@fake_qq.on_terminal("n")
async def _(text: str):
    # 空一行
    print()


@fake_qq.on_terminal("d")
async def delay(text: str):
    # 延时
    try:
        n = float(text.strip())
    except:
        n = 1
    await asyncio.sleep(n)


@fake_qq.on_terminal("dn")
async def _(text: str):
    # 延时并空一行
    await delay(text)
    print()


@fake_qq.on_terminal("g")
async def _(text: str):
    # 群聊
    items = text.split(" ", maxsplit=2)
    if len(items) == 3:
        await fake_qq.send_group(*items)


@fake_qq.on_terminal("p")
async def dd_(text: str):
    # 私聊
    items = text.split(" ", maxsplit=1)
    if len(items) == 2:
        await fake_qq.send_private(*items)


@fake_qq.on_terminal("s")
async def _(text: str):
    args = shlex.split(text)
    # 自动化脚本
    for dirpath in ["", "scripts"]:
        path = Path(dirpath, f"{args[0]}.ini")
        if path.is_file():
            break
    else:
        fake_qq.print("脚本不存在")
        return

    with path.open("r", encoding="utf8") as f:
        data = f.read()

    # 替换所有变量
    rs = re.findall(r"\$\d+", data)
    for r in rs:
        i = int(r[1:])
        if i >= 0 and i < len(args):
            data = data.replace(f"${i}", args[i])

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
    show = True
    before = ""
    after = ""
    for line in lines:
        if line == "hide":
            show = False
            continue

        cmd, text = divide(line)
        if cmd == "after":
            after = text
            continue

        if cmd == "before":
            before = text
            continue

        if before:
            await fake_qq.deal_line(before)

        if show:
            print(line)

        await fake_qq.deal_line(line)

        if after:
            await fake_qq.deal_line(after)


@fake_qq.on_terminal("h")
async def _(text: str):
    fake_qq.print_help()


@fake_qq.on_terminal("sa")
async def _(text: str):
    if text == "on":
        open_sample()
        fake_qq.print("已打开cqhttp采样")
    else:
        close_sample()
        fake_qq.print("已关闭cqhttp采样")
