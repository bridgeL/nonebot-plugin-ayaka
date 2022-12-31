from sqlalchemy import MetaData
from pathlib import Path
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine
from sqlalchemy.orm import declarative_base

from nonebot import get_driver
from nonebot.params import Depends

from .helpers import ensure_dir_exists

driver = get_driver()


def get_echo():
    '''等级比DEBUG还低时，才会回显sql语句'''
    log_level = driver.config.log_level
    if isinstance(log_level, int):
        return log_level < 10
    return logger.level(log_level) < logger.level("DEBUG")


ensure_dir_exists(Path("data", "ayaka"))
_engine = create_async_engine(
    url="sqlite+aiosqlite:///data/ayaka/ayaka.db",
    echo=get_echo(), future=True
)
_metadata_obj = MetaData()


@driver.on_startup
async def on_startup():
    async with _engine.begin() as conn:
        await conn.run_sync(_metadata_obj.create_all)
    logger.success("data source initialized")


@driver.on_shutdown
async def on_shutdown():
    await _engine.dispose()
    logger.success("data source disposed")


def get_metadata_obj():
    '''获得metadata

    示例代码:
    ```
        metadata = get_metadata_obj()
        user_table = Table(
            "user",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("name", String),
        )
    ```
    '''
    return _metadata_obj


def get_orm_engine():
    '''获得engine对象'''
    return _engine


def OrmEngine() -> AsyncEngine:
    '''获得engine对象'''
    return Depends(get_orm_engine)


def get_orm_session():
    '''获得session对象

    示例代码:
    ```
        async with get_orm_session() as session:
            # use it!
            await session.execute()
    ```
    '''
    return AsyncSession(_engine, expire_on_commit=False)


async def _get_orm_session():
    async with AsyncSession(_engine, expire_on_commit=False) as session:
        yield session
        await session.commit()


def OrmSession() -> AsyncSession:
    '''获得session对象'''
    return Depends(_get_orm_session)
