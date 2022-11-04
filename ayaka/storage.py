
import json
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Any
# from .config import AYAKA_DEBUG

if TYPE_CHECKING:
    from .ayaka import AyakaApp


class AyakaParser:
    @classmethod
    def unstr(self, text: str):
        return text

    @classmethod
    def str(self, data) -> str:
        return str(data)


class AyakaJsonParser(AyakaParser):
    @classmethod
    def unstr(self, text: str):
        return json.loads(text)

    @classmethod
    def str(self, data) -> str:
        return json.dumps(data, ensure_ascii=False)


class AyakaFile:
    '''文件路径'''

    def __init__(self, func: Callable[[], Path], default=None, parser=AyakaParser) -> None:
        self._path = None
        self.func = func
        self.default = default
        self.parser = parser

    @property
    def path(self):
        if not self._path:
            path = self.func()
            if not path.exists() and self.default is not None:
                text = self.parser.str(self.default)
                with path.open("w+", encoding="utf8") as f:
                    f.write(text)
            self._path = path
        return self._path

    def load(self):
        with self.path.open("r", encoding="utf8") as f:
            text = f.read()
        data = self.parser.unstr(text)
        return data

    def save(self, data):
        text = self.parser.str(data)
        with self.path.open("w+", encoding="utf8") as f:
            f.write(text)


class AyakaJsonDataAccessor:
    def __init__(self, file: "AyakaJsonFile", keys: list) -> None:
        self.file = file
        self._keys = [str(k) for k in keys]

    def keys(self, *keys):
        return AyakaJsonDataAccessor(self.file, *self._keys, *keys)

    @property
    def last_key(self):
        if self._keys:
            return self._keys[-1]

    def get(self, default=None):
        data = self.file.load()
        for key in self._keys:
            if key not in data:
                return default
            data = data[key]
        return data

    def set(self, data):
        if self._keys:
            d = origin = self.file.load()
            for key in self._keys[:-1]:
                if key not in d:
                    d[key] = {}
                d = d[key]
            d[self.last_key] = data
            data = origin
        self.file.save(data)
        return data


class AyakaJsonFile(AyakaFile):
    '''json文件路径'''

    def __init__(self, func: Callable[[], Path], default={}) -> None:
        super().__init__(func, default, AyakaJsonParser)

    def load(self) -> Any:
        return super().load()

    def keys(self, *keys):
        return AyakaJsonDataAccessor(self, keys)


class AyakaDir:
    '''文件夹路径'''

    def __init__(self, func: Callable[[], Path]) -> None:
        self.func = func
        self._path = None

    @property
    def path(self):
        if not self._path:
            path = self.func()
            if not path.exists():
                path.mkdir(parents=True)
            self._path = path
        return self._path

    def iterdir(self):
        return self.path.iterdir()

    def file(self, name, default=None):
        def func():
            path = self.path / str(name)
            return path
        return AyakaFile(func, default)

    def json(self, name, default={}):
        def func():
            path = self.path / str(name)
            path = path.with_suffix(".json")
            return path
        return AyakaJsonFile(func, default)


class AyakaStorage:
    def __init__(self, app: "AyakaApp") -> None:
        self.app = app

    def plugin(self, *names):
        '''路径基准点 <app_file>/../'''
        def func():
            _names = [str(name) for name in names]
            path = Path(self.app.path.parent, *_names)
            return path
        return AyakaDir(func)

    def group(self, *names):
        '''路径基准点 data/groups/<bod_id>/<group_id>/<app.name>/'''
        def func():
            _names = [
                "data", "groups",
                self.app.bot_id,
                self.app.group_id,
                self.app.name,
                *names
            ]
            _names = [str(name) for name in _names]
            path = Path(*_names)
            return path
        return AyakaDir(func)
