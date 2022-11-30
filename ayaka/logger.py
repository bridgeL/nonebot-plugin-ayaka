'''便于之后拓展与迁移'''
from loguru import logger
from .config import ayaka_root_config

# ayaka bot配置
if ayaka_root_config.bot_type == "ayakabot":
    import sys
    logger.remove()
    logger.add(
        sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> \t| <blue>{name}</blue> - {message}", level="DEBUG", backtrace=False, diagnose=False
    )

# 通用配置
logger.add(
    open("error.log", "a+", encoding="utf8"),
    level="ERROR", backtrace=False, diagnose=False
)
