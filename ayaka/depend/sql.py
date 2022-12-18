import os
import sqlite3
from typing import TYPE_CHECKING, List, Type

from loguru import logger
from ..config import ayaka_data_path, ayaka_root_config

if TYPE_CHECKING:
    from .db import AyakaDB

PrimaryKey = {"primary": True}
JsonKey = {"json": True}

path = ayaka_data_path / "ayaka.db"
journal_path = ayaka_data_path / "ayaka.db-journal"
old_journal_path = ayaka_data_path / "ayaka.db-journal-old"
db = sqlite3.connect(path)


def log_query(query, values=None):
    if ayaka_root_config.debug:
        logger.debug(query)
        if values:
            logger.debug(values)


def execute(query, values=None):
    log_query(query, values)
    if values is None:
        cursor = db.execute(query)
    else:
        cursor = db.execute(query, values)
    cursor.close()


def executemany(query, values=None):
    log_query(query, values)
    if values is None:
        cursor = db.executemany(query)
    else:
        cursor = db.executemany(query, values)
    cursor.close()


def fetchall(query: str):
    cursor = db.execute(query)
    values = cursor.fetchall()
    cursor.close()
    log_query(query, values)
    return values


def create_table(name: str, cls: Type["AyakaDB"]):
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


def insert_or_replace(name: str, data: "AyakaDB", action: str):
    keys = list(data.dict().keys())
    values = list(data.dict().values())
    keys_str = ",".join(keys)
    values_str = ("(?),"*len(keys))[:-1]
    query = f"{action} into \"{name}\" ({keys_str}) values ({values_str})"
    execute(query, values)


def insert_or_replace_many(name: str, datas: List["AyakaDB"], action: str):
    data = datas[0]
    keys = list(data.dict().keys())
    values = [[getattr(data, k) for k in keys] for data in datas]
    keys_str = ",".join(keys)
    values_str = ("(?),"*len(keys))[:-1]
    query = f"{action} into \"{name}\" ({keys_str}) values ({values_str})"
    executemany(query, values)


def select_many(name: str, cls: Type["AyakaDB"], where: str = ""):
    props = cls.props()
    keys = list(props.keys())
    if where:
        where = f"where {where}"

    keys_str = ",".join(keys)
    query = f"select {keys_str} from \"{name}\" {where}"
    values = fetchall(query)

    # 组装为字典
    datas = [
        cls._create_by_db_data({k: v for k, v in zip(keys, vs)})
        for vs in values
    ]
    return datas


def drop_table(name: str):
    query = f"drop table if exists \"{name}\""
    execute(query)


def commit():
    if old_journal_path.exists():
        os.remove(old_journal_path)
        logger.debug("已删除旧db-journal-old文件")
    if journal_path.exists():
        if ayaka_root_config.debug:
            logger.debug("commit")
        logger.debug("更新数据库")
        db.commit()

        # 提交失败，直接删除
        if journal_path.exists():
            logger.debug("更新数据库失败，已将journal文件更名为db-journal-old")
            journal_path.rename(old_journal_path)


def wrap(v):
    if isinstance(v, str):
        return f"\"{v}\""
    return str(v)
