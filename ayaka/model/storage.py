'''
目前使用json

之后过渡到sql
'''
import json
from pathlib import Path
from typing import List


def list_2_lines(data: list):
    lines = ["\t" + json.dumps(d,  ensure_ascii=False) + "," for d in data]
    lines[-1] = lines[-1][:-1]
    return lines


def dict_2_lines(data: dict):
    def get_line(k, v):
        return "\t" + \
            json.dumps(k, ensure_ascii=False) + ":" + \
            json.dumps(v, ensure_ascii=False) + ","
    lines = [get_line(k, v) for k, v in data.items()]
    lines[-1] = lines[-1][:-1]
    return lines


def beauty_save(path, data):
    if type(path) is str:
        path = Path(path)

    if type(data) is list:
        with path.open("w+", encoding="utf8") as f:
            f.write("[\n")
            lines = list_2_lines(data)
            for line in lines:
                f.write(line + "\n")
            f.write("]\n")

    if type(data) is dict:
        with path.open("w+", encoding="utf8") as f:
            f.write("{\n")
            lines = dict_2_lines(data)
            for line in lines:
                f.write(line + "\n")
            f.write("}\n")


def create_path(*path_str):
    '''创建文件所在目录'''
    path_str = [str(s) for s in path_str]
    path = Path(*path_str)
    if not path.exists():
        path.mkdir(parents=True)
    return path


def create_file(*path_str, default):
    path = create_path(*path_str[:-1]).joinpath(path_str[-1])
    if not path.exists():
        with path.open("w+", encoding="utf8") as f:
            f.write(default)
    return path


class StorageAccessor:
    def __init__(self, path: Path, keys: List[str]) -> None:
        self.path = path
        self.keys = keys

    def inc(self):
        '''+1s'''
        data = self.get()
        if data is None:
            self.set(1)
        else:
            self.set(data+1)

    def set(self, _data):
        with self.path.open("r", encoding="utf8") as f:
            # 读取文件
            data = json.load(f)

            # 留着后续保存
            origin = data

            # 赋值
            for key in self.keys[:-1]:
                if key not in data:
                    data[key] = {}
                data = data[key]

            data[self.keys[-1]] = _data

        # 保存文件
        beauty_save(self.path, origin)

    def get(self, default=None):
        with self.path.open("r", encoding="utf8") as f:
            # 读取文件
            data = json.load(f)

            # 查找值
            for key in self.keys:
                if key in data:
                    data = data[key]
                else:
                    return default

        # 返回
        return data


class Storage:
    '''持久化数据'''

    def __init__(self, *path_str, default="") -> None:
        self.path = create_file(*path_str, default=default)

    def accessor(self, *keys):
        keys = [str(k) for k in keys]
        return StorageAccessor(self.path, keys)


class Cache:
    '''临时数据'''

    def __setattr__(self, name, value):
        self.__dict__[name] = value
