import sqlite3
from typing import List, Type, Union
from typing_extensions import Self
from pydantic import BaseModel

db = sqlite3.connect("ayaka.db")


def create_table(name: str, cls: Type[BaseModel]):
    props: dict = cls.schema()["properties"]
    args = [f"{k} {v['type']}" for k, v in props.items()]

    primarys = []
    for k, v in props.items():
        if v.get("extra", {}).get("primary"):
            primarys.append(k)

    if primarys:
        primarys_str = ",".join(f"\"{k}\"" for k in primarys)
        args.append(f"PRIMARY KEY({primarys_str})")

    args_str = ",\n".join(args)
    query = f"create table if not exists \"{name}\" ({args_str})"
    db.execute(query)


def insert_or_replace(name: str, data: BaseModel, action: str):
    keys = list(data.dict().keys())
    values = list(data.dict().values())
    keys_str = ",".join(keys)
    values_str = ("(?),"*len(keys))[:-1]
    query = f"{action} into \"{name}\" ({keys_str}) values ({values_str})"
    db.execute(query, values)


def insert_or_replace_many(name: str, datas: List[BaseModel], action: str):
    data = datas[0]
    keys = list(data.dict().keys())
    values = [[getattr(data, k) for k in keys] for data in datas]
    keys_str = ",".join(keys)
    values_str = ("(?),"*len(keys))[:-1]
    query = f"{action} into \"{name}\" ({keys_str}) values ({values_str})"
    db.executemany(query, values)


def insert(name: str, data: BaseModel):
    insert_or_replace(name, data, "insert")


def replace(name: str, data: BaseModel):
    insert_or_replace(name, data, "replace")


def insert_many(name: str, datas: List[BaseModel]):
    insert_or_replace_many(name, datas, "insert")


def replace_many(name: str, datas: List[BaseModel]):
    insert_or_replace_many(name, datas, "replace")


def select_many(name: str, cls: Type[BaseModel], where: str = "1"):
    props: dict = cls.schema()["properties"]
    keys = list(props.keys())
    # keys_str = ",".join(keys)
    query = f"select * from \"{name}\" where {where}"
    cursor = db.cursor()
    cursor.execute(query)
    values = cursor.fetchall()
    cursor.close()

    # 组装为字典
    datas = [cls(**{k: v for k, v in zip(keys, vs)}) for vs in values]
    return datas


def drop_table(name: str):
    query = f"drop table if exists \"{name}\""
    db.execute(query)


def commit():
    db.commit()


def wrap(v):
    if isinstance(v, str):
        return f"\"{v}\""
    return str(v)

# [-]
# 有没有办法，在类继承的时候，让类调用一个回调，从而自动进行create_table


class AyakaDB(BaseModel):
    '''继承时要书写`__table_name__`

    设置主键需要 <name>:<type> = Field(extra={"primary": True})'''
    __table_name__ = ""

    def __init__(self, **data) -> None:
        if not self.__table_name__:
            raise Exception("__table_name__不可为空")
        super().__init__(**data)

    @classmethod
    def drop_table(cls):
        drop_table(cls.__table_name__)

    @classmethod
    def create_table(cls):
        create_table(cls.__table_name__, cls)

    @classmethod
    def replace(cls, data: Self):
        replace(cls.__table_name__, data)

    @classmethod
    def replace_many(cls, datas: List[Self]):
        replace_many(cls.__table_name__, datas)

    @classmethod
    def insert(cls, data: Self):
        insert(cls.__table_name__, data)

    @classmethod
    def insert_many(cls, datas: List[Self]):
        insert_many(cls.__table_name__, datas)

    @classmethod
    def select_many(cls, **params) -> List[Self]:
        if not params:
            where = "1"
        else:
            where = " and ".join(f"{k}={wrap(v)}" for k, v in params.items())
        return select_many(cls.__table_name__, cls, where)

    @classmethod
    def select_one(cls, **params) -> Union[Self, None]:
        datas = cls.select_many(**params)
        if datas:
            return datas[0]
