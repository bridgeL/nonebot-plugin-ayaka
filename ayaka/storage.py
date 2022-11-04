
import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .ayaka import AyakaApp


class AyakaStorage:
    def __init__(self, app: "AyakaApp") -> None:
        self.app = app

    def plugin_path(self, *names):
        '''路径基准点 <app_file>/../'''
        names = [str(name) for name in names]
        path = Path(self.app.path.parent, *names)
        return AyakaPath(path)

    def group_path(self, *names):
        '''路径基准点 data/groups/<bod_id>/<group_id>/<app.name>/'''
        names = [
            "data", "groups",
            self.app.bot_id,
            self.app.group_id,
            self.app.name,
            *names
        ]
        names = [str(name) for name in names]
        path = Path(*names)
        return AyakaPath(path)


class AyakaPath:
    '''文件夹路径'''

    def __init__(self, path: Path) -> None:
        self.path = path
        if not path.exists():
            path.mkdir(parents=True)

    def iterdir(self):
        return self.path.iterdir()

    def file(self, name, default=None):
        path = self.path / str(name)
        if not path.exists() and default is not None:
            with path.open("w+", encoding="utf8") as f:
                f.write(str(default))
        return AyakaFile(path)

    def json(self, name, default={}):
        path = self.path / str(name)
        path = path.with_suffix(".json")
        if not path.exists():
            with path.open("w+", encoding="utf8") as f:
                json.dump(default, f, ensure_ascii=False)
        return AyakaJsonFile(path)


class AyakaFile:
    '''文件路径'''

    def __init__(self, path: Path):
        self.path = path

    def load(self):
        with self.path.open("r", encoding="utf8") as f:
            data = f.read()
        return data

    def save(self, data):
        with self.path.open("w+", encoding="utf8") as f:
            f.write(str(data))


class AyakaJsonFile:
    def __init__(self, path: Path, *keys) -> None:
        self.path = path
        self.keys = [str(k) for k in keys]

    def chain(self, *keys):
        return AyakaJsonFile(self.path, *self.keys, *keys)

    def load(self):
        with self.path.open("r", encoding="utf8") as f:
            data = json.load(f)
        return data

    def save(self, data):
        with self.path.open("w+", encoding="utf8") as f:
            json.dump(data, f, ensure_ascii=False)

    def get(self, default=None):
        data = self.load()
        for k in self.keys:
            if k not in data:
                return default
            data = data[k]
        return data

    def set(self, value):
        if not self.keys:
            self.save(value)
            return value

        data = origin = self.load()
        for k in self.keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]
        data[self.keys[-1]] = value
        self.save(origin)
        return value
