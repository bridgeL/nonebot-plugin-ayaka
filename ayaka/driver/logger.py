from loguru import logger
from ..config import ayaka_root_config

# ayakabot配置
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

# 展示配置
logger.success(f"已读取ayaka根配置 {ayaka_root_config.dict()}")
