from typing import TYPE_CHECKING, Dict
from pydantic import BaseModel

if TYPE_CHECKING:
    from ..ayaka import AyakaApp


class AyakaDepend(BaseModel):
    @classmethod
    async def _create_by_app(cls, app: "AyakaApp"):
        raise NotImplementedError

    @classmethod
    def props(cls) -> Dict[str, dict]:
        return cls.schema()["properties"]
