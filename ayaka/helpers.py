import re
from time import time
from pathlib import Path
from pydantic import BaseModel

from nonebot import get_driver
from nonebot.adapters.onebot.v11 import MessageSegment, Message

driver = get_driver()


def ensure_dir_exists(path: str | Path):
    '''确保输入的目录路径存在'''
    if not isinstance(path, Path):
        path = Path(path)
    if not path.exists():
        path.mkdir(parents=True)


async def do_nothing():
    '''什么也不做，可以当个占位符'''
    pass


def singleton(cls):
    '''单例模式的装饰器'''
    instance = None

    def getinstance(*args, **kwargs):
        nonlocal instance
        if instance is None:
            instance = cls(*args, **kwargs)
        return instance

    return getinstance


def run_in_startup(func):
    '''等效于driver.on_startup(func)'''
    driver.on_startup(func)
    return func


class Timer:
    '''计时器

    示例代码:
    ```
        with Timer("test"):
            # some code...

        # 输出：[test] 耗时2.02s
    ```
    '''

    def __init__(self, name) -> None:
        self.name = name

    def __enter__(self):
        self.time = time()

    def __exit__(self, a, b, c):
        diff = time() - self.time
        print(f"[{self.name}] 耗时{diff:.2f}s")


class SimpleUserInfo(BaseModel):
    '''简单用户信息'''
    id: int
    name: str


def find_user_by_uid(users: list, uid: int):
    for user in users:
        if uid == user["user_id"]:
            return user


def find_user_by_uname(users: list, uname: str):
    for user in users:
        _uname = user["card"] or user["nickname"]
        if _uname == uname:
            return user


def get_user(m: MessageSegment, users: list):
    '''根据MessageSegment，自动通过uid/uname/[CQ:at]/@xxx四种可能的查找方式开始搜索对应user的信息'''
    str_m = str(m)

    # [CQ:at]
    if m.type == "at":
        user = find_user_by_uid(users, int(m.data["qq"]))

    elif m.type != "text":
        return

    # uid
    elif re.search(r"^\d+$", str_m):
        user = find_user_by_uid(users, int(str_m))

    # @xxx
    elif str_m.startswith("@"):
        user = find_user_by_uname(users, str_m[1:])

    # uname
    else:
        user = find_user_by_uname(users, str_m)

    if user:
        uid = user["user_id"]
        uname = user["card"] or user["nickname"]
        return SimpleUserInfo(id=uid, name=uname)


class StrOrMsgList(list[str | MessageSegment]):
    '''将Message对象转为list[str | MessageSegment]'''
    seps = driver.config.command_sep
    seps = [re.escape(sep) for sep in seps]
    patt = re.compile("|".join(seps))

    @classmethod
    def create(cls, msg: Message):
        items = StrOrMsgList()
        for m in msg:
            if m.type == "text":
                ts = cls.patt.split(str(m))
                items.extend(t for t in ts if t)
            else:
                items.append(m)
        return items
