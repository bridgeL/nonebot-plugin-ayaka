from typing import Dict
from pydantic import BaseModel


class AyakaDepend(BaseModel):
    @classmethod
    async def create(cls, **kwargs):
        raise NotImplementedError

    @classmethod
    def props(cls) -> Dict[str, dict]:
        return cls.schema()["properties"]
