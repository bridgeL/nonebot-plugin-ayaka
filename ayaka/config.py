'''便于之后拓展与迁移'''
import platform
from .driver import get_driver

INIT_STATE = "init"
AYAKA_DEBUG = 0

driver = get_driver()

# 命令抬头
prefix = getattr(driver.config, "ayaka_prefix", "#")

# 参数分割符
sep = getattr(driver.config, "ayaka_separate", " ")
if not sep:
    print("ayaka的分割符不可设置为空")
    raise

# 是否排除go-cqhttp缓存的过期消息
exclude_old = getattr(driver.config, "ayaka_exclude_old", True)

# 是否开启fastapi-reload
fastapi_reload = getattr(driver.config, "fastapi_reload", True)

running_on_windows = platform.system() == "Windows"
