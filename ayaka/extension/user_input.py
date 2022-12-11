import re
from typing import Optional
from pydantic import BaseModel, Field
from ..ayaka import AyakaApp
from ..depend import AyakaInput
from ..driver import MessageSegment


def find_user_by_uid(users: list, uid: int):
    for user in users:
        if uid == user["user_id"]:
            return user


def find_user_by_uname(users: list, uname: str):
    for user in users:
        _uname = user["card"] or user["nickname"]
        if _uname == uname:
            return user


async def get_user(app: AyakaApp, at: MessageSegment):
    str_at = str(at)
    users = await app.bot.get_group_member_list(group_id=app.group_id)

    if at.type == "at":
        user = find_user_by_uid(users, int(at.data["qq"]))
    elif at.type != "text":
        return
    elif re.search(r"^\d+$", str_at):
        user = find_user_by_uid(users, int(str_at))
    elif str_at.startswith("@"):
        user = find_user_by_uname(users, str_at[1:])
    else:
        user = find_user_by_uname(users, str_at)

    if user:
        uid = user["user_id"]
        uname = user["card"] or user["nickname"]
        return User(id=uid, name=uname)


class User(BaseModel):
    id: int
    name: str


class UserInput(AyakaInput):
    '''将用户输入的第一个参数（QQ号/群名片/@xxx）自动转换为User对象'''
    user: Optional[User] = Field(description="查询目标的QQ号/名称/@xx")

    @classmethod
    async def create_by_app_get_params(cls, app: AyakaApp):
        args = app.args
        props = cls.props()
        params = {k: v for k, v in zip(props, args)}
        if args:
            params["user"] = await get_user(app, args[0])
        return params
