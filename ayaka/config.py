'''
    管理插件配置，读写ayaka_setting.json文件
'''

import json
import platform
from pathlib import Path
from pydantic import BaseModel, ValidationError
from typing import List
from .driver import get_driver
from .logger import logger

total_settings: dict = {}
setting_filepath = Path("ayaka_setting.json")
if not setting_filepath.exists():
    with setting_filepath.open("w+", encoding="utf8") as f:
        f.write("{}")

with setting_filepath.open("r", encoding="utf8") as f:
    total_settings = json.load(f)


def create_ayaka_plugin_config_base(app_name):
    class AyakaPluginConfigBase(BaseModel):
        def __init__(self):
            try:
                super().__init__(**total_settings.get(app_name, {}))
            except ValidationError as e:
                logger.error(
                    f"导入配置失败，请检查 ayaka_setting.json 中，{app_name}的配置是否正确")
                raise e
            self.__save__()

        def __setattr__(self, name, value):
            super().__setattr__(name, value)
            self.__save__()

        def __save__(self):
            total_settings[app_name] = self.dict()
            with setting_filepath.open("w+", encoding="utf8") as f:
                json.dump(total_settings, f, ensure_ascii=0, indent=4)

    return AyakaPluginConfigBase


INIT_STATE = "init"
AYAKA_DEBUG = 0

BaseConfig = create_ayaka_plugin_config_base("__root__")


class Config(BaseConfig):
    version: str = "0.4.4b0"
    prefix: str = "#"
    separate: str = " "
    exclude_old_msg: bool = True
    owners: List[int] = []
    admins: List[int] = []


ayaka_root_config = Config()
logger.success(f"已读取ayaka根配置 {ayaka_root_config.dict()}")

# 命令抬头
prefix = ayaka_root_config.prefix

# 参数分割符
sep = ayaka_root_config.separate
if not sep:
    logger.error("ayaka的分割符不可设置为空")
    raise

# 是否排除go-cqhttp缓存的过期消息
exclude_old = ayaka_root_config.exclude_old_msg

# 是否开启fastapi-reload
fastapi_reload = getattr(get_driver().config, "fastapi_reload", True)

running_on_windows = platform.system() == "Windows"
