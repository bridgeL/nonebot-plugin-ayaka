from typing import TYPE_CHECKING
from pydantic import ValidationError, validator
from .depend import AyakaDepend
from ..driver import MessageSegment

if TYPE_CHECKING:
    from ..ayaka import AyakaApp


class AyakaInput(AyakaDepend):
    '''解析命令行参数为对应成员属性

    注意：每个成员属性都必须标注类型，否则可能解析顺序出错'''
    @classmethod
    async def _create_by_app(cls, app: "AyakaApp"):
        args = app.args
        props = cls.props()
        data = {k: v for k, v in zip(props, args)}
        try:
            return cls(**data)
        except ValidationError as e:
            await app.bot.send_group_msg(group_id=app.group_id, message=str(e))

    @classmethod
    def help(cls):
        props = cls.props()
        data = {k: v.get("description", "") for k, v in props.items()}
        return data

    @validator("*", pre=True)
    def __all_validator__(cls, v: MessageSegment):
        if v.type == "text":
            return v.data["text"]
        return v
