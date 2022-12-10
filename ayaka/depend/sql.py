import sqlite3
from typing import List, Type
from .depend import AyakaDepend
from ..config import ayaka_data_path, ayaka_root_config

PrimaryKey = {"primary": True}
JsonKey = {"json": True}

path = ayaka_data_path / "ayaka.db"
db = sqlite3.connect(path)


def execute(query, values=None):
    if ayaka_root_config.debug:
        print(query)
        if values:
            print(values)
    if values is None:
        cursor = db.execute(query)
    else:
        cursor = db.execute(query, values)
    cursor.close()


def executemany(query, values=None):
    if ayaka_root_config.debug:
        print(query)
        if values:
            print(values)
    if values is None:
        cursor = db.executemany(query)
    else:
        cursor = db.executemany(query, values)
    cursor.close()


def fetchall(query):
    cursor = db.execute(query)
    values = cursor.fetchall()
    cursor.close()
    if ayaka_root_config.debug:
        print(query)
        print(values)
    return values


def create_table(name: str, cls: Type[AyakaDepend]):
    props = cls.props()
    args = []
    primarys = []

    for k, v in props.items():
        extra: dict = v.get("extra", {})
        if extra.get("primary"):
            primarys.append(k)
        if extra.get("json"):
            args.append(f"{k} text")
        else:
            args.append(f"{k} {v['type']}")

    if primarys:
        primarys_str = ",".join(f"\"{k}\"" for k in primarys)
        args.append(f"PRIMARY KEY({primarys_str})")

    args_str = ",\n".join(args)
    query = f"create table if not exists \"{name}\" ({args_str})"

    execute(query)


def insert_or_replace(name: str, data: AyakaDepend, action: str):
    keys = list(data.dict().keys())
    values = list(data.dict().values())
    keys_str = ",".join(keys)
    values_str = ("(?),"*len(keys))[:-1]
    query = f"{action} into \"{name}\" ({keys_str}) values ({values_str})"
    execute(query, values)


def insert_or_replace_many(name: str, datas: List[AyakaDepend], action: str):
    data = datas[0]
    keys = list(data.dict().keys())
    values = [[getattr(data, k) for k in keys] for data in datas]
    keys_str = ",".join(keys)
    values_str = ("(?),"*len(keys))[:-1]
    query = f"{action} into \"{name}\" ({keys_str}) values ({values_str})"
    executemany(query, values)


def select_many(name: str, cls: Type[AyakaDepend], where: str = "1"):
    props = cls.props()
    keys = list(props.keys())
    
    # 本来想用*，不过为了保险起见（后续更新的兼容性），还是老老实实写key吧
    keys_str = ",".join(keys)
    query = f"select {keys_str} from \"{name}\" where {where}"
    values = fetchall(query)

    # 组装为字典
    datas = [cls(**{k: v for k, v in zip(keys, vs)}) for vs in values]
    return datas


def drop_table(name: str):
    query = f"drop table if exists \"{name}\""
    execute(query)


def commit():
    if ayaka_root_config.debug:
        print("commit")
    db.commit()


def wrap(v):
    if isinstance(v, str):
        return f"\"{v}\""
    return str(v)