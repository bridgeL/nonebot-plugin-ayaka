'''群组缓存'''
from .json_ctrl import AbstractJsonCtrl


class AyakaCacheCtrl(AbstractJsonCtrl):
    '''ayaka缓存控制器，其数据空间在各群组、各插件间相互独立'''

    def __repr__(self) -> str:
        return f"AyakaCacheCtrl({self.get()})"

    def __init__(self, data=None, *keys) -> None:
        self._data = {} if data is None else data
        self._keys = [str(k) for k in keys]

    def _load(self):
        return self._data

    def _save(self, data):
        self._data = data

    def chain(self, *keys):
        return AyakaCacheCtrl(self._data, *self._keys, *keys)

    # 兼容旧API
    def __getattr__(self, k):
        return self.chain(k).get()

    # 兼容旧API
    def __setattr__(self, k, v):
        if k in ["_data", "_keys"]:
            super().__setattr__(k, v)
        else:
            self.chain(k).set(v)
