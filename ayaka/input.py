from typing import Dict, List
from pydantic import BaseModel, validator
from .driver import MessageSegment


class AyakaInput(BaseModel):
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
    def __all_validator__(cls, v: MessageSegment):
        if v.type == "text":
            return v.data["text"]
        return v
