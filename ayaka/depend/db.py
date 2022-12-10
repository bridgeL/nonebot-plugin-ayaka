import json
from pydantic import Field
from typing import List, TYPE_CHECKING
from typing_extensions import Self
from .depend import AyakaDepend
from .sql import PrimaryKey, JsonKey, insert_or_replace, create_table, drop_table, insert_or_replace_many, select_many, wrap, db

if TYPE_CHECKING:
    from .. import AyakaApp


class AyakaDB(AyakaDepend):
    '''
```
1. 继承时要书写 __table_name__
2. 如果要把该类放入回调函数的参数表中，则还要编写classmethod async def create方法
3. 设置主键需要使用
    <name>:<type> = Field(extra=AyakaDB.__primary_key__)
4. 一些特殊类型的数据请设置其为json形式存取 
    <name>:<type> = Field(extra=AyakaDB.__json_key__)
    AyakaDB在写入时会自动序列化该数据为字符串，写入数据库，读取时则相反
5. 若需要编写自定义读写数据方法，可以使用AyakaDB.get_db()方法获取sqlite3.Connection对象
6. 使用前先调用classmethod def create_table
```
'''
    __table_name__ = ""
    __primary_key__ = PrimaryKey
    __json_key__ = JsonKey

    def __init__(self, **data) -> None:
        if not self.__table_name__:
            raise Exception("__table_name__不可为空")
        super().__init__(**data)

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
        '''根据数据类型自动创建表'''
        create_table(cls.__table_name__, cls)

    @classmethod
    def replace(cls, data: Self):
        insert_or_replace(cls.__table_name__, data, "replace")

    def save(self):
        '''写入数据库'''
        self.replace(self)

    @classmethod
    def replace_many(cls, datas: List[Self]):
        insert_or_replace_many(cls.__table_name__, datas, "replace")

    @classmethod
    def insert(cls, data: Self):
        insert_or_replace(cls.__table_name__, data, "insert")

    @classmethod
    def insert_many(cls, datas: List[Self]):
        insert_or_replace_many(cls.__table_name__, datas, "insert")

    @classmethod
    def select_many(cls, **params) -> List[Self]:
        '''按照params的值搜索数据，返回数据列表，若没有符合的数据则返回空列表'''
        where = "1"
        if params:
            where = " and ".join(f"{k}={wrap(v)}" for k, v in params.items())
        return select_many(cls.__table_name__, cls, where)

    @classmethod
    def select_one(cls, **params):
        '''按照params的值搜索数据，返回一项数据，若不存在，则自动根据params创建'''
        datas = cls.select_many(**params)
        if datas:
            return datas[0]
        data = cls(**params)
        data.save()
        return data

    @classmethod
    def get_db(cls):
        return db


class AyakaGroupDB(AyakaDB):
    '''继承时要书写`__table_name__`

    主键有且仅有 group_id

    使用前先调用classmethod def create_table'''
    group_id: int = Field(extra=AyakaDB.__primary_key__)

    @classmethod
    async def _create_by_app(cls, app: "AyakaApp"):
        return cls.select_one(group_id=app.group_id)


class AyakaUserDB(AyakaDB):
    '''继承时要书写`__table_name__`

    主键有且仅有 group_id, user_id

    使用前先调用classmethod def create_table'''
    group_id: int = Field(extra=AyakaDB.__primary_key__)
    user_id: int = Field(extra=AyakaDB.__primary_key__)

    @classmethod
    async def _create_by_app(cls, app: "AyakaApp"):
        return cls.select_one(
            group_id=app.group_id,
            user_id=app.user_id
        )
