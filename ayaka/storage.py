
import json
from pathlib import Path
from typing import TYPE_CHECKING
from .config import AYAKA_DEBUG

if TYPE_CHECKING:
    from .ayaka import AyakaApp


class AyakaStorage:
    def __init__(self, app: "AyakaApp") -> None:
        self.app = app

    def plugin(self, *names):
        '''返回路径'''
        return AyakaPath(
            self.app.path.parent,
            *names
        )

    def group(self, *names):
        '''返回路径'''
        return AyakaPath(
            "data",
            "groups",
            self.app.bot_id,
            self.app.group_id,
            self.app.name,
            *names
        )


class AyakaPath:
    def __repr__(self) -> str:
        return f"AyakaPath({self.path})"

    def __init__(self, *names) -> None:
        names = [str(name) for name in names]
        self.path = Path(*names)
        if not self.path.exists():
            self.path.mkdir(parents=True)
        if AYAKA_DEBUG:
            print(self)

    def iterdir(self):
        return self.path.iterdir()

    def jsonfile(self, name: str, default={}):
        '''可以不写文件名后缀'''
        return AyakaJsonFile(self.path, name, default)

    def file(self, name: str, default=None):
        '''需要输入文件名后缀'''
        return AyakaFile(self.path, name, default)


class AyakaJsonFile:
    def __repr__(self) -> str:
        return f"AyakaJsonFile({self.path})"

    def __init__(self, path: Path, name, default) -> None:
        self.path = path.joinpath(name).with_suffix(".json")
        if not self.path.exists():
            self.save(default)
        if AYAKA_DEBUG:
            print(self)

    def load(self):
        with self.path.open("r", encoding="utf8") as f:
            data = json.load(f)
        return data

    def save(self, data):
        with self.path.open("w+", encoding="utf8") as f:
            json.dump(data, f, ensure_ascii=False)

    def keys(self, *keys):
        return AyakaJsonDataAccessor(self.path, keys)


class AyakaFile:
    def __repr__(self) -> str:
        return f"AyakaFile({self.path})"

    def __init__(self, path: Path, name, default) -> None:
        self.path = path.joinpath(name)
        if not self.path.exists() and default is not None:
            self.save(default)
        if AYAKA_DEBUG:
            print(self)

    def load(self):
        with self.path.open("r", encoding="utf8") as f:
            data = f.read()
        return data

    def save(self, data):
        with self.path.open("w+", encoding="utf8") as f:
            f.write(str(data))


class AyakaJsonDataAccessor:
    def __repr__(self) -> str:
        return f"AyakaJsonDataAccessor({self.path}, {self.keys})"

    def __init__(self, path: Path, keys: list) -> None:
        self.path = path
        self.keys = [str(k) for k in keys]
        if AYAKA_DEBUG:
            print(self)

    @property
    def last_key(self):
        if self.keys:
            return self.keys[-1]

    def get(self, default=None):
        with self.path.open("r", encoding="utf8") as f:
            data = json.load(f)
        for key in self.keys:
            if key not in data:
                return default
            data = data[key]
        return data

    def set(self, data):
        if not self.keys:
            with self.path.open("w+", encoding="utf8") as f:
                json.dump(data, f, ensure_ascii=False)
        else:
            with self.path.open("r", encoding="utf8") as f:
                dd = json.load(f)
            d = dd
            for key in self.keys[:-1]:
                if key not in d:
                    d[key] = {}
                d = d[key]
            d[self.last_key] = data
            with self.path.open("w+", encoding="utf8") as f:
                json.dump(dd, f, ensure_ascii=False)
