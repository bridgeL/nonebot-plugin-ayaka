'''初始化方法，封装在这里，没必要外部使用'''
# ---- 方便生成api文档 ----
import nonebot
from loguru import logger
try:
    nonebot.get_driver()
except:
    logger.warning("ayaka意外地提前加载，其本应在nonebot2完成初始化之后才加载")
    nonebot.init()

# ---- 其他初始化工作 ----
from . import master
from . import log

DONT_USE_ME = ""
