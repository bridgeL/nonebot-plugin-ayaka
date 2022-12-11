from typing import TYPE_CHECKING, Union
from typing_extensions import Self
from pydantic import ValidationError, validator
from .depend import AyakaDepend
from ..driver import MessageSegment

if TYPE_CHECKING:
    from ..ayaka import AyakaApp


class AyakaInput(AyakaDepend):
    '''解析命令行参数为对应成员属性

    注意：每个成员属性都必须标注类型，否则可能解析顺序出错'''
    @classmethod
    async def create_by_app(cls, app: "AyakaApp") -> Union[Self, None]:
        '''可用于重构'''
        params = await cls.create_by_app_get_params(app)
        try:
            return cls(**params)
        except ValidationError as e:
            return await cls.create_by_app_deal_exc(app, e)

    @classmethod
    async def create_by_app_get_params(cls, app: "AyakaApp") -> dict:
        '''可用于重构'''
        args = app.args
        props = cls.props()
        return {k: v for k, v in zip(props, args)}

    @classmethod
    async def create_by_app_deal_exc(cls, app: "AyakaApp", e: ValidationError) -> Union[Self, None]:
        '''可用于重构'''
        # await app.bot.send_group_msg(group_id=app.group_id, message=str(e))
        print(e)

    @classmethod
    def help(cls) -> dict:
        props = cls.props()
        data = {k: v.get("description", "") for k, v in props.items()}
        return data

    @validator("*", pre=True)
    def __all_validator__(cls, v):
        if isinstance(v, MessageSegment) and v.type == "text":
            return v.data["text"]
        return v
