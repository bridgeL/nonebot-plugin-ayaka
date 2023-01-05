'''仍然是旧版的自定义sql orm

未来计划1.1.0 替换为sqlmodel

不建议其他人用，以后会大改'''
import asyncio
import os
import json
import sqlite3
from typing import Literal
from typing_extensions import Self

from .helpers import run_in_startup
from .lazy import get_driver, Field, BaseModel, logger
from .config import data_path

PrimaryKey = {"primary": True}
JsonKey = {"json": True}

database_path = data_path / "ayaka.db"
journal_path = data_path / "ayaka.db-journal"
old_journal_path = data_path / "ayaka.db-journal-old"
db = sqlite3.connect(database_path)

driver = get_driver()


def get_echo():
    '''等级比DEBUG还低时，才会回显sql语句'''
    log_level = driver.config.log_level
    if isinstance(log_level, int):
        return log_level < 10
    return logger.level(log_level) < logger.level("DEBUG")


echo = get_echo()


def log_query(query, values=None):
    if echo:
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


table_names = []


def create_table(name: str, cls: type["AyakaDB"]):
    if not name:
        raise Exception("__table_name__不可为空")

    if name in table_names:
        return
    table_names.append(name)

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


def insert_or_replace(name: str, data: "AyakaDB", action: Literal["insert", "replace"]):
    create_table(name, data.__class__)

    keys = list(data.dict().keys())
    values = list(data.dict().values())
    keys_str = ",".join(keys)
    values_str = ("(?),"*len(keys))[:-1]
    query = f"{action} into \"{name}\" ({keys_str}) values ({values_str})"
    execute(query, values)


def insert_or_replace_many(name: str, datas: list["AyakaDB"], action: Literal["insert", "replace"]):
    create_table(name, datas[0].__class__)

    data = datas[0]
    keys = list(data.dict().keys())
    values = [[getattr(data, k) for k in keys] for data in datas]
    keys_str = ",".join(keys)
    values_str = ("(?),"*len(keys))[:-1]
    query = f"{action} into \"{name}\" ({keys_str}) values ({values_str})"
    executemany(query, values)


def delete(name: str, cls: type["AyakaDB"], extra: str = ""):
    create_table(name, cls)
    query = f"delete from \"{name}\" {extra}"
    execute(query)


def select_many(name: str, cls: type["AyakaDB"], extra: str = ""):
    create_table(name, cls)

    props = cls.props()
    keys = list(props.keys())
    keys_str = ",".join(keys)
    query = f"select {keys_str} from \"{name}\" {extra}"
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


async def loop():
    while True:
        commit()
        await asyncio.sleep(10)


@run_in_startup
async def create_loop():
    asyncio.create_task(loop())


def commit():
    if old_journal_path.exists():
        os.remove(old_journal_path)
        logger.debug("已删除旧db-journal-old文件")
    if journal_path.exists():
        logger.debug("更新数据库")
        db.commit()

        # 提交失败，直接删除
        if journal_path.exists():
            logger.debug("更新数据库失败，已将journal文件更名为db-journal-old")
            journal_path.rename(old_journal_path)


def wrap(v):
    '''给字符串包裹上双引号'''
    if isinstance(v, str):
        return f"\"{v}\""
    return str(v)


class AyakaDB(BaseModel):
    '''
    ```
    1. 继承时要书写 __table_name__
    2. 如果要把该类放入回调函数的参数表中，则还要编写classmethod async def create_by_app方法
    3. 设置主键需要使用
        <name>:<type> = Field(extra=AyakaDB.__primary_key__)
    4. 一些特殊类型的数据请设置其为json形式存取 
        <name>:<type> = Field(extra=AyakaDB.__json_key__)
        AyakaDB在写入时会自动序列化该数据为字符串，写入数据库，读取时则相反
    5. 若需要编写自定义读写数据方法，可以使用AyakaDB.get_db()方法获取sqlite3.Connection对象
    ```
    '''
    __table_name__ = ""
    __primary_key__ = PrimaryKey
    __json_key__ = JsonKey

    @classmethod
    def props(cls) -> dict[str, dict]:
        return cls.schema()["properties"]

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        self.save()

    @classmethod
    def _create_by_db_data(cls, data: dict):
        props = cls.props()

        # 特殊处理json
        for k, v in props.items():
            extra: dict = v.get("extra", {})
            if extra.get("json"):
                if k in data:
                    data[k] = json.loads(data[k])

        return cls(**data)

    def dict(self, **params):
        data = super().dict(**params)
        props = self.props()

        # 特殊处理json
        for k, v in props.items():
            extra: dict = v.get("extra", {})
            if extra.get("json"):
                if k in data:
                    data[k] = json.dumps(data[k], ensure_ascii=0)
        return data

    @classmethod
    def drop_table(cls):
        drop_table(cls.__table_name__)

    @classmethod
    def create_table(cls):
        '''[已过时的API] 根据数据类型自动创建表'''
        create_table(cls.__table_name__, cls)

    @classmethod
    def replace(cls, data: Self):
        insert_or_replace(cls.__table_name__, data, "replace")

    @classmethod
    def replace_many(cls, datas: list[Self]):
        insert_or_replace_many(cls.__table_name__, datas, "replace")

    @classmethod
    def insert(cls, data: Self):
        insert_or_replace(cls.__table_name__, data, "insert")

    @classmethod
    def insert_many(cls, datas: list[Self]):
        insert_or_replace_many(cls.__table_name__, datas, "insert")

    @classmethod
    def delete(cls, **params) -> list[Self]:
        '''按照params的值删除数据，若params为空，则删除全部'''
        extra = ""
        if params:
            where = " and ".join(
                f"{k}={wrap(v)}"
                for k, v in params.items()
            )
            extra = f"where {where}"

        return delete(cls.__table_name__, cls, extra)

    @classmethod
    def select_many(cls, **params) -> list[Self]:
        '''按照params的值搜索数据，返回数据列表，若没有符合的数据则返回空列表

        若params为空，则返回表内所有数据'''

        extra = ""
        if params:
            where = " and ".join(
                f"{k}={wrap(v)}"
                for k, v in params.items()
            )
            extra = f"where {where}"

        return select_many(cls.__table_name__, cls, extra)

    @classmethod
    def select_one(cls, **params):
        '''按照params的值搜索数据，返回一项数据，若不存在，则自动根据params创建，创建后自动写入数据库'''
        datas = cls.select_many(**params)
        if datas:
            return datas[0]

        # 不存在则新建
        data = cls(**params)
        cls.replace(data)
        return data

    @classmethod
    def get_db(cls):
        '''获取connection对象，通过该方法你可以自定义一些crud方法'''
        return db

    def save(self):
        '''写入数据库'''
        self.replace(self)


class AyakaGroupDB(AyakaDB):
    '''继承时要书写`__table_name__`

    主键 group_id'''
    group_id: int = Field(extra=AyakaDB.__primary_key__)


class AyakaUserDB(AyakaDB):
    '''继承时要书写`__table_name__`

    主键 group_id, user_id'''
    group_id: int = Field(extra=AyakaDB.__primary_key__)
    user_id: int = Field(extra=AyakaDB.__primary_key__)
