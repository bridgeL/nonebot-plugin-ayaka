'''
    管理插件配置，提供读写支持
'''
import json
from pathlib import Path
from pydantic import BaseModel, ValidationError
from loguru import logger

from .helpers import ensure_dir_exists

AYAKA_VERSION = "1.0.0"

data_path = Path("data", "ayaka")
ensure_dir_exists(data_path)


class AyakaConfig(BaseModel):
    '''继承时请填写`__config_name__`

    该配置保存在data/ayaka/<__config_name__>.json

    在修改不可变成员属性时，`AyakaConfig`会自动写入到本地文件，但修改可变成员属性时，需要手动执行save函数
    '''
    __config_name__ = ""

    def __init__(self):
        name = self.__config_name__
        if not name:
            raise Exception("__config_name__不可为空")

        # 默认空数据
        data = {}

        try:
            path = data_path / f"{name}.json"
            # 存在则读取
            if path.exists():
                with path.open("r", encoding="utf8") as f:
                    data = json.load(f)

            # 载入数据
            super().__init__(**data)

        except ValidationError as e:
            logger.error(
                f"导入配置失败，请检查{name}的配置是否正确")
            raise e

        # 强制更新（更新默认值）
        self.save()
        logger.opt(colors=True).debug(f"已自动载入配置文件 <c>{name}</c>")

    def __setattr__(self, name, value):
        if getattr(self, name) != value:
            super().__setattr__(name, value)
            self.save()
            logger.opt(colors=True).debug(f"已自动写入配置更改 <c>{name}</c>")

    def save(self):
        '''修改可变成员变量后，需要使用该方法才能保存其值到文件'''
        name = self.__config_name__
        data = self.dict()
        path = data_path / f"{name}.json"
        with path.open("w+", encoding="utf8") as f:
            json.dump(data, f, ensure_ascii=0, indent=4)


class RootConfig(AyakaConfig):
    '''根配置'''
    __config_name__ = "root"
    version: str = AYAKA_VERSION


ayaka_root_config = RootConfig()
ayaka_root_config.version = AYAKA_VERSION
logger.opt(colors=True).success(f"ayaka当前版本 <y>{AYAKA_VERSION}</y>")


def load_data_from_file(path: Path):
    '''从指定文件加载数据

    参数:
    
        path: 文件路径。文件类型，必须是.json文件或.txt文件

    返回:
    
        json反序列化后的结果(对应.json文件) 或 字符串数组(对应.txt文件)

    异常:
    
        错误的文件类型
    '''
    if path.suffix not in [".json", ".txt"]:
        raise Exception("错误的文件类型")

    if path.suffix == ".json":
        with path.open("r", encoding="utf8") as f:
            return json.load(f)
    else:
        with path.open("r", encoding="utf8") as f:
            # 排除空行
            return [line[:-1] for line in f if line[:-1]]
