'''提供一些有益的方法和类'''
import asyncio
import functools
import hashlib
import json
import re
from time import time

import httpx
from .lazy import get_driver, Message, MessageSegment, BaseModel, Path, logger

driver = get_driver()


def ensure_list(data: str | list | tuple | set):
    '''确保为列表'''
    if isinstance(data, str):
        return [data]
    if isinstance(data, list):
        return data
    return list(data)


def ensure_dir_exists(path: str | Path):
    '''确保目录存在

    参数：

        path：文件路径或目录路径

            若为文件路径，该函数将确保该文件父目录存在

            若为目录路径，该函数将确保该目录存在

    返回：

        Path对象
    '''
    if not isinstance(path, Path):
        path = Path(path)
    # 文件
    if path.suffix:
        ensure_dir_exists(path.parent)
    # 目录
    elif not path.exists():
        path.mkdir(parents=True)
    return path


async def do_nothing():
    '''什么也不做，可以当个占位符'''
    pass


def slow_load_config(cls):
    '''配置对象将在fastapi启动后才加载，且将该类转换为单例模式'''
    return run_in_startup(singleton(cls))


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

    def __init__(self, name: str = "", show: bool = True) -> None:
        self.name = name
        self.diff = 0
        self.show = show

    def __enter__(self):
        self.time = time()

    def __exit__(self, a, b, c):
        self.diff = time() - self.time
        if self.show:
            print(f"[{self.name}] 耗时{self.diff:.2f}s")


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


@singleton
def _get_split_patt():
    seps = driver.config.command_sep
    seps = [re.escape(sep) for sep in seps]
    return re.compile("|".join(seps))


def _command_args(msg: Message) -> list[str | MessageSegment]:
    '''根据配置的分割符，分割消息为数组'''
    items = []
    for m in msg:
        if m.type == "text":
            ts = _get_split_patt().split(str(m))
            items.extend(t for t in ts if t)
        else:
            items.append(m)
    return items


def pack_messages(user_id: int, user_name: str, messages: list):
    '''转换为cqhttp node格式'''
    data = [
        MessageSegment.node_custom(
            user_id=user_id,
            nickname=user_name,
            content=str(m)
        )
        for m in messages
    ]
    return data


def load_data_from_file(path: str | Path):
    '''从指定文件加载数据

    参数:

        path: 文件路径

        若文件类型为json，按照json格式读取

        若文件类型为其他，则按行读取，并排除空行

    返回:

        json反序列化后的结果(对应.json文件) 或 字符串数组(对应.txt文件)
    '''
    path = ensure_dir_exists(path)
    if not path.exists():
        raise Exception(f"文件不存在 {path}")

    with path.open("r", encoding="utf8") as f:
        if path.suffix == ".json":
            return json.load(f)
        else:
            # 排除空行
            return [line[:-1] for line in f if line[:-1]]


def is_async_callable(obj) -> bool:
    '''抄自 starlette._utils.is_async_callable

    判断对象是否可异步调用'''
    while isinstance(obj, functools.partial):
        obj = obj.func

    return asyncio.iscoroutinefunction(obj) or (
        callable(obj) and asyncio.iscoroutinefunction(obj.__call__)
    )


async def download_url(url: str) -> bytes:
    '''返回指定链接下载的字节流数据'''
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=20)
        resp.raise_for_status()
        return resp.content


async def resource_download(url: str, path: str | Path = ""):
    '''异步下载资源到指定位置

    参数：

        url：资源网址

        path：本地下载位置

    返回：

        下载得到的字节数据
        
    异常：

        下载异常
    '''
    if path:
        path = ensure_dir_exists(path)
        logger.debug(f"下载文件 {path} ...")

    logger.info(f"拉取数据 {url} ...")
    data = await download_url(url)

    # 保存
    if path:
        path.write_bytes(data)

    return data


def get_file_hash(path: str | Path):
    path = ensure_dir_exists(path)
    return hashlib.md5(path.read_bytes()).hexdigest()


class ResItem(BaseModel):
    '''资源项'''
    path: str
    '''下载地址的相对地址尾'''
    hash: str
    '''资源的哈希值'''


class ResInfo(BaseModel):
    '''资源信息'''
    base: str
    '''下载地址的绝对地址头'''
    items: list[ResItem]
    '''资源项'''


async def resource_download_by_res_info(res_info: ResInfo, base_dir: str | Path):
    '''根据res_info，异步下载资源到指定位置，只下载哈希值发生变化的资源项

    参数：

        res_info：资源信息

        base_dir：本地文件地址

    返回：

        是否存在更新
    '''
    if isinstance(base_dir, str):
        base_dir = Path(base_dir)

    has_updated = False
    for item in res_info.items:
        url = res_info.base + "/" + item.path
        path = base_dir / item.path
        if not path.exists() or get_file_hash(path) != item.hash:
            await resource_download(url, path)
            has_updated = True

    return has_updated
