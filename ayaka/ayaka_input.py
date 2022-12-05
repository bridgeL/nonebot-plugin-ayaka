from typing import Dict, List
from pydantic import BaseModel, validator
from .driver import MessageSegment


class TypedMessageSegment(MessageSegment):
    __type__ = ""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, MessageSegment):
            raise TypeError('MessageSegment required')
        if v.type != cls.__type__:
            raise ValueError('invalid MessageSegment format')
        return v

    # @classmethod
    # def __modify_schema__(cls, field_schema):
    #     field_schema.update(
    #         pattern='^[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}$',
    #         examples=['SP11 9DG', 'w1j7bu'],
    #     )


def msg_type(type: str):
    class _TypedMessageSegment(TypedMessageSegment):
        __type__ = type
    return _TypedMessageSegment


class AyakaInputModel(BaseModel):
    def __init__(self, args: List[MessageSegment]) -> None:
        props = self.schema()["properties"]
        data = {k: v for k, v in zip(props, args)}
        super().__init__(**data)

    @classmethod
    def help(cls):
        props: Dict[str, dict] = cls.schema()["properties"]
        data = {k: v.get("description") for k, v in props.items()}
        return data

    @validator("*", pre=True)
    def test(cls, v: MessageSegment):
        if v.type == "text":
            return v.data["text"]
        return v
