from typing import TYPE_CHECKING, Dict
from pydantic import BaseModel

if TYPE_CHECKING:
    from ..ayaka import AyakaApp


class AyakaDepend(BaseModel):
    @classmethod
    async def create_by_app(cls, app: "AyakaApp"):
        return

    @classmethod
    def props(cls) -> Dict[str, dict]:
        return cls.schema()["properties"]
