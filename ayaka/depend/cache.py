'''群组缓存'''
from typing import TYPE_CHECKING
from .depend import AyakaDepend
from ..config import ayaka_root_config

if TYPE_CHECKING:
    from ..ayaka import AyakaApp


class AyakaCache(AyakaDepend):
    '''Ayaka缓存 以群组为单位相互独立'''
    class Config:
        arbitrary_types_allowed = True

    @classmethod
    async def _create_by_app(cls, app: "AyakaApp"):
        cache = app.cache
        name = cls.__name__
        if name not in cache:
            if ayaka_root_config.debug:
                print(f"初始化缓存 {cls.__name__}")
            cache[name] = cls()
        return cache[name]
