'''1.0.1b0

https://bridgel.github.io/ayaka_doc/1.0.1/
'''
# ---- 方便生成api文档 ----
try:
    from nonebot import get_driver
    get_driver()
except:
    import nonebot
    nonebot.init()
# ----  ----

# ---- ayaka box ----
from .box import AyakaBox
from .config import AyakaConfig, load_data_from_file
from .helpers import get_user, do_nothing, singleton, run_in_startup, Timer
from .orm import AyakaDB, AyakaGroupDB, AyakaUserDB

# ---- 方便使用 ----
from .lazy import *

# ---- master ----
from . import master
