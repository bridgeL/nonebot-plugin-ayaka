'''提供一些有益的方法和类'''
import re
from time import time
from importlib import import_module
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
    '''确保输入的目录路径存在'''
    if not isinstance(path, Path):
        path = Path(path)
    if not path.exists():
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


def load_cwd_plugins(path: Path | str):
    if isinstance(path, str):
        path = Path(path)
    name = ".".join(path.parts)
    for p in path.iterdir():
        module_name = name + "." + p.stem
        try:
            import_module(module_name)
        except:
            logger.exception(f"导入{module_name}失败")
