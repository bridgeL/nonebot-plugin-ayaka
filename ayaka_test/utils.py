import re
import base64
from pathlib import Path


def record(text: str):
    path = Path("ayaka_test.log")
    text = text.replace("<", "&lt;")
    with path.open("a+", encoding="utf8") as f:
        f.write(text + "\n")


def divide(line):
    if " " not in line:
        line += " "
    cmd, text = line.split(" ", maxsplit=1)
    return cmd, text


def shorten(args):
    # 限制长度
    text = " ".join(str(a)[:3000] for a in args)

    # 保护已闭合的标签
    text = re.sub(r"<(.*)>(.*?)</(\1)>", r"%%%\1%%%\2%%%/\1%%%", text)
    # 注释未闭合的标签
    text = re.sub(r"<.*?>", r"\\\g<0>", text)
    # 恢复已闭合的标签
    text = re.sub(r"%%%(.*)%%%(.*?)%%%/(\1)%%%", r"<\1>\2</\1>", text)
    return text


def base64_to_pic(base64_str):
    base64_str = re.sub("^.*?base64://", "", base64_str)
    base64_bs = base64.b64decode(base64_str)

    # 固定名称
    name = '1.png'

    path = Path("temp", "image", name)
    if not path.parent.exists():
        path.parent.mkdir(parents=True)
    with path.open('wb') as f:
        f.write(base64_bs)
    return str(path)
