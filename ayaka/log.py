'''
临时关闭对ayaka插件无意义的Duplicated prefix rule warning提示，在ayaka插件加载完毕后恢复该警告提示
'''
import sys
from typing import TYPE_CHECKING
from nonebot.log import default_format, logger_id, logger
from .box import prevent_duplicated_warning

if TYPE_CHECKING:
    from loguru import Record


def default_filter(record: "Record"):
    log_level = record["extra"].get("nonebot_log_level", "INFO")
    levelno = logger.level(log_level).no if isinstance(
        log_level, str) else log_level
    if record["level"].no < levelno:
        return False
    if prevent_duplicated_warning["value"] and "Duplicated prefix rule" in record["message"]:
        return False
    return True


logger.remove(logger_id)
logger_id = logger.add(
    sys.stdout,
    level=0,
    diagnose=False,
    filter=default_filter,
    format=default_format,
)
