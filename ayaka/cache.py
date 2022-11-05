from .json_ctrl import AbstractJsonCtrl


class AyakaCacheCtrl(AbstractJsonCtrl):
    '''ayaka缓存控制器，其数据空间在各群组、各插件间相互独立'''

    def __repr__(self) -> str:
        return f"AyakaCacheCtrl({self.get()})"

    def __init__(self, data=None, *keys) -> None:
        self.data = {} if data is None else data
        self.keys = [str(k) for k in keys]

    def _load(self):
        return self.data

    def _save(self, data):
        self.data = data

    def chain(self, *keys):
        return AyakaCacheCtrl(self.data, *self.keys, *keys)

    # 兼容旧API
    def __getattr__(self, k):
        return self.chain(k).get()

    # 兼容旧API
    def __setattr__(self, k, v):
        if k in ["data", "keys"]:
            super().__setattr__(k, v)
        else:
            self.chain(k).set(v)
