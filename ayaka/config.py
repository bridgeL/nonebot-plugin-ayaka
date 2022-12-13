'''
    管理插件配置，读写ayaka_setting.json文件
'''

import json
from pathlib import Path
from pydantic import BaseModel, ValidationError, validator
from typing import List, Literal
from loguru import logger

AYAKA_VERSION = "0.5.4b0"

# 总文件夹
ayaka_data_path = Path("data", "ayaka")
if not ayaka_data_path.exists():
    ayaka_data_path.mkdir(parents=1)

# 分文件夹
ayaka_data_separate_path = ayaka_data_path / "separate"
if not ayaka_data_separate_path.exists():
    ayaka_data_separate_path.mkdir(parents=1)

# 总配置文件
setting_filepath = ayaka_data_path / "ayaka_setting.json"
# 总配置
total_settings: dict = {}
# 数据脏标志
dirty_flag = False


def load():
    global total_settings
    if not setting_filepath.exists():
        with setting_filepath.open("w+", encoding="utf8") as f:
            f.write("{}")
        total_settings = {}
    else:
        logger.debug("加载配置文件")
        with setting_filepath.open("r", encoding="utf8") as f:
            total_settings = json.load(f)


def save():
    global dirty_flag
    if dirty_flag:
        logger.debug("更新配置文件")
        with setting_filepath.open("w+", encoding="utf8") as f:
            json.dump(total_settings, f, ensure_ascii=0, indent=4)
        dirty_flag = False


load()


class AyakaConfig(BaseModel):
    '''继承时请填写`__app_name__`

    该配置保存在data/ayaka/ayaka_setting.json中字典的`__app_name__`键下

    当配置项较多时（超过100行），建议使用`AyakaLargeConfig`

    在修改不可变成员属性时，`AyakaConfig`会自动写入到本地文件，但修改可变成员属性时，需要手动执行save函数
    '''
    __app_name__ = ""
    __separate__ = False

    def __init__(self):
        name = self.__app_name__
        if not name:
            raise Exception("__app_name__不可为空")

        # 默认空数据
        data = {}

        try:
            if self.__separate__:
                path = ayaka_data_separate_path / f"{name}.json"
                # 存在则读取
                if path.exists():
                    with path.open("r", encoding="utf8") as f:
                        data = json.load(f)

            # 存在则读取
            elif name in total_settings:
                data = total_settings[name]

            # 载入数据
            super().__init__(**data)

        except ValidationError as e:
            logger.error(
                f"导入配置失败，请检查{name}的配置是否正确")
            raise e

        # 强制更新（更新默认值）
        self.save()

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        self.save()
        logger.debug("已自动保存配置更改")

    def force_update(self):
        '''修改可变成员变量后，需要使用该方法才能保存其值到文件'''
        self.save()

    def save(self):
        '''修改可变成员变量后，需要使用该方法才能保存其值到文件'''
        name = self.__app_name__
        if self.__separate__:
            data = self.dict()
            path = ayaka_data_separate_path / f"{name}.json"
            with path.open("w+", encoding="utf8") as f:
                json.dump(data, f, ensure_ascii=0, indent=4)
        else:
            total_settings[name] = self.dict()
            global dirty_flag
            dirty_flag = True


class AyakaLargeConfig(AyakaConfig):
    '''继承时请填写`__app_name__`

    该配置保存在data/ayaka/separate/`__app_name__`.json下

    在修改不可变成员属性时，`AyakaLargeConfig`会自动写入到本地文件，但修改可变成员属性时，需要手动执行save函数
    '''
    __app_name__ = ""
    __separate__ = True


class Config(AyakaConfig):
    __app_name__ = "__root__"
    version: str = AYAKA_VERSION
    # 命令抬头
    prefix: str = "#"
    # 参数分割符
    separate: str = " "
    # 是否排除go-cqhttp缓存的过期消息
    exclude_old_msg: bool = True
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
