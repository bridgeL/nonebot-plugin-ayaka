import asyncio
from pathlib import Path
import re
import shlex
from typing import Dict
from .core import fake_qq, divide
from .sample import open_sample, close_sample


def shell_parse(text: str):
    ts = shlex.split(text)
    params: Dict[str, list] = {}
    args = []
    k = None
    for t in ts:
        if t.startswith("-"):
            k = t.lstrip("-")
            if k not in params:
                params[k] = []
        elif k is None:
            args.append(t)
        else:
            params[k].append(t)
            k = None
    return params, args


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
    params, args = shell_parse(text)

    # 脚本名称
    script_name = params.get("n")
    if not script_name:
        fake_qq.print("-n <脚本名称>")
        return

    script_name = script_name[0]
    path = Path("script", script_name)

    # 插件名称
    plugin_name = params.get("p")
    if plugin_name:
        plugin_name = plugin_name[0]
        path = Path("plugins", plugin_name).joinpath(path)

    path = path.with_suffix(".ini")
    if not path.is_file():
        fake_qq.print("脚本不存在")
        return

    with path.open("r", encoding="utf8") as f:
        data = f.read()

    # 替换所有变量
    rs = re.findall(r"\$\d+", data)
    nums = list(set(int(r[1:]) for r in rs))
    for i in nums:
        if i >= 1 and i <= len(args):
            data = data.replace(f"${i}", args[i-1])

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
