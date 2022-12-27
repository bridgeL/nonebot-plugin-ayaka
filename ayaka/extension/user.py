import re
from pydantic import BaseModel
from nonebot.adapters.onebot.v11 import MessageSegment


class SimpleUserInfo(BaseModel):
    id: int
    name: str

    def __init__(self, user_id, card, nickname, **data) -> None:
        super().__init__(
            id=user_id,
            name=card or nickname
        )


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
    str_m = str(m)

    if m.type == "at":
        user = find_user_by_uid(users, int(m.data["qq"]))

    elif m.type != "text":
        return

    elif re.search(r"^\d+$", str_m):
        user = find_user_by_uid(users, int(str_m))

    elif str_m.startswith("@"):
        user = find_user_by_uname(users, str_m[1:])

    else:
        user = find_user_by_uname(users, str_m)

    if user:
        uid = user["user_id"]
        uname = user["card"] or user["nickname"]
        return SimpleUserInfo(id=uid, name=uname)
