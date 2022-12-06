'''
    管理插件配置，读写ayaka_setting.json文件
'''

import json
from pathlib import Path
from pydantic import BaseModel, ValidationError, validator
from typing import List, Literal
from loguru import logger

AYAKA_VERSION = "0.5.0"

total_settings: dict = {}
setting_filepath = Path("ayaka_setting.json")
if not setting_filepath.exists():
    with setting_filepath.open("w+", encoding="utf8") as f:
        f.write("{}")

with setting_filepath.open("r", encoding="utf8") as f:
    total_settings = json.load(f)


class AyakaPluginConfig(BaseModel):
    __app_name__ = ""

    def __init__(self):
        try:
            super().__init__(**total_settings.get(self.__app_name__, {}))
        except ValidationError as e:
            logger.error(
                f"导入配置失败，请检查 ayaka_setting.json 中，{self.__app_name__}的配置是否正确")
            raise e
        self.force_update()

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        self.force_update()

    def force_update(self):
        total_settings[self.__app_name__] = self.dict()
        with setting_filepath.open("w+", encoding="utf8") as f:
            json.dump(total_settings, f, ensure_ascii=0, indent=4)


def create_ayaka_plugin_config_base(app_name):
    class _AyakaPluginConfig(AyakaPluginConfig):
        __app_name__ = app_name
    return _AyakaPluginConfig


BaseConfig = create_ayaka_plugin_config_base("__root__")


class Config(BaseConfig):
    version: str = AYAKA_VERSION
    # 命令抬头
    prefix: str = "#"
    # 参数分割符
    separate: str = " "
    # 是否排除go-cqhttp缓存的过期消息
    exclude_old_msg: bool = True
    # 是否使用playwright
    use_playwright: bool = False
    # ayaka插件的所有者
    owners: List[int] = []
    # ayaka插件的管理者
    admins: List[int] = []
    # 切换bot类型
    bot_type: Literal["nonebot", "ayakabot"] = "nonebot"
    # 是否处于调试模式
    debug: bool = False
    # 端口号
    ayaka_port: int = 19900

    @validator('separate')
    def name_must_contain_space(cls, v):
        if not v:
            logger.warning("ayaka的分割符被设置为空字符串，这会使得ayaka无法正确分割参数")
        return v


ayaka_root_config = Config()
ayaka_root_config.version = AYAKA_VERSION
