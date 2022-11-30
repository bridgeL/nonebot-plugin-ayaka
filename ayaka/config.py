'''
    管理插件配置，读写ayaka_setting.json文件
'''

import json
from pathlib import Path
from pydantic import BaseModel, ValidationError, validator
from typing import List, Literal
from loguru import logger

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

        def force_update(self):
            self.__save__()

    return AyakaPluginConfigBase


INIT_STATE = "init"
AYAKA_DEBUG = 0

BaseConfig = create_ayaka_plugin_config_base("__root__")


class Config(BaseConfig):
    version: str = "0.4.4b0"
    # 命令抬头
    prefix: str = "#"
    # 参数分割符
    separate: str = " "
    # 是否排除go-cqhttp缓存的过期消息
    exclude_old_msg: bool = True
    # 是否使用playwright
    use_playwright: bool = True
    # ayaka插件的所有者
    owners: List[int] = []
    # ayaka插件的管理者
    admins: List[int] = []
    # 切换bot类型
    bot_type: Literal["nonebot", "ayakabot"] = "nonebot"

    @validator('separate')
    def name_must_contain_space(cls, v):
        if not v:
            logger.warning("ayaka的分割符不可设置为空，已强制设置为空格")
            return " "
        return v


ayaka_root_config = Config()
logger.success(f"已读取ayaka根配置 {ayaka_root_config.dict()}")
