import platform
from .driver import get_driver

INIT_STATE = "init"
AYAKA_DEBUG = 0

driver = get_driver()

# 命令抬头
prefix = getattr(driver.config, "ayaka_prefix", None)
if prefix is None:
    ps = list(driver.config.command_start)
    prefix = ps[0] if len(ps) else "#"

# 参数分割符
sep = getattr(driver.config, "ayaka_separate", None)
if sep is None:
    ss = list(driver.config.command_sep)
    sep = ss[0] if len(ss) else " "

# 是否排除go-cqhttp缓存的过期消息
exclude_old = getattr(driver.config, "ayaka_exclude_old", True)

# 是否开启fastapi-reload
fastapi_reload = getattr(driver.config, "fastapi_reload", True)

running_on_windows = platform.system() == "Windows"
