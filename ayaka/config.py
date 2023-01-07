'''
    管理插件配置，提供读写支持
'''
import json
from pydantic import ValidationError
from .helpers import ensure_dir_exists
from .lazy import logger, BaseModel, Path

AYAKA_VERSION = "1.0.3b0"

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
                f"导入配置失败，请检查{name}的配置是否正确；如果不确定出错的原因，可以尝试更新插件-删除配置-重启bot")
            raise e

        # 强制更新（更新默认值）
        self.save()
        logger.opt(colors=True).debug(f"已载入配置文件 <g>{name}</g>")

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
'''ayaka根配置，目前是吉祥物，仅标识ayaka的版本号'''

ayaka_root_config.version = AYAKA_VERSION
logger.opt(colors=True).success(f"<y>ayaka</y> 当前版本 <y>{AYAKA_VERSION}</y>")
