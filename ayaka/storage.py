
import json
from pathlib import Path
from typing import TYPE_CHECKING
from .json_ctrl import AbstractJsonCtrl

if TYPE_CHECKING:
    from .ayaka import AyakaApp


class AyakaStorage:
    '''中间层，方便后续拓展，比如aiosqlite(?'''

    def __init__(self, app: "AyakaApp") -> None:
        self.app = app

    def plugin_path(self, *names):
        '''获取路径 <create_app_file>/../*names'''
        names = [str(name) for name in names]
        path = Path(self.app.path.parent, *names)
        return AyakaPath(path)

    def group_path(self, *names):
        '''获取路径 data/groups/<bod_id>/<group_id>/<app.name>/*names'''
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

    def __init__(self, path=Path("test")) -> None:
        self.path = path
        if not path.exists():
            path.mkdir(parents=True)

    def iterdir(self):
        return self.path.iterdir()

    def file(self, name, default=None):
        path = self.path / str(name)
        file = AyakaFile(path)
        if not path.exists() and default is not None:
            file.save(default)
        return file

    def json(self, name, default={}):
        path = self.path / str(name)
        path = path.with_suffix(".json")
        file = AyakaJsonFile(path)
        if not path.exists():
            file.save(default)
        return file


class AyakaFile:
    '''文件'''

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
    '''JSON文件'''

    def __init__(self, path: Path) -> None:
        self.path = path

    def chain(self, *keys):
        return AyakaJsonFileCtrl(self.path, *keys)

    def load(self):
        with self.path.open("r", encoding="utf8") as f:
            data = json.load(f)
        return data

    def save(self, data):
        with self.path.open("w+", encoding="utf8") as f:
            json.dump(data, f, ensure_ascii=False)


class AyakaJsonFileCtrl(AbstractJsonCtrl):
    '''AyakaJsonFileCtrl实际上可兼容替代AyakaJsonFile，但是为了避免语义上的混乱，仍分作两个类'''

    def __init__(self, path: Path, *keys) -> None:
        self.path = path
        self.keys = [str(k) for k in keys]

    def _load(self):
        with self.path.open("r", encoding="utf8") as f:
            data = json.load(f)
        return data

    def _save(self, data):
        with self.path.open("w+", encoding="utf8") as f:
            json.dump(data, f, ensure_ascii=False)

    def chain(self, *keys):
        return AyakaJsonFileCtrl(self.path, *self.keys, *keys)
