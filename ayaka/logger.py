'''便于之后拓展与迁移'''
from loguru import logger

logger.add(open("error.log", "a+", encoding="utf8"), level="ERROR", backtrace=False, diagnose=False)
