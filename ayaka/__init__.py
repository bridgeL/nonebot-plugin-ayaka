'''1.0.1b1

https://bridgel.github.io/ayaka_doc/1.0.1/
'''
# ---- 方便生成api文档 ----
def _ensure_nb_init():
    import nonebot
    from loguru import logger
    try:
        nonebot.get_driver()
    except:
        logger.warning("ayaka意外地提前加载，其本应在nonebot2完成初始化之后才加载")
        nonebot.init()
        
_ensure_nb_init()

# ---- ayaka box ----
from .box import AyakaBox
from .config import AyakaConfig, load_data_from_file
from .helpers import Timer, get_user, do_nothing, singleton, run_in_startup, slow_load_config, load_cwd_plugins

# ---- 未来将被sqlmodel取代 ----
from .orm import AyakaDB, AyakaGroupDB, AyakaUserDB

# ---- 懒人包 ----
from .lazy import *

# ---- 其他初始化工作 ----
def _other_init():
    from . import master
    from . import log

_other_init()
