import sys
from typing import TYPE_CHECKING
from nonebot.log import default_format, logger_id, logger

if TYPE_CHECKING:
    from loguru import Record


def default_filter(record: "Record"):
    '''关闭恼人的duplicated warning提示'''
    log_level = record["extra"].get("nonebot_log_level", "INFO")
    levelno = logger.level(log_level).no if isinstance(
        log_level, str) else log_level
    return record["level"].no >= levelno and not "Duplicated" in record["message"]


logger.remove(logger_id)
logger_id = logger.add(
    sys.stdout,
    level=0,
    diagnose=False,
    filter=default_filter,
    format=default_format,
)
logger.opt(colors=True).warning(
    "<y>duplicated prefix warning</y> 已被 <c>ayaka</c> 关闭")
