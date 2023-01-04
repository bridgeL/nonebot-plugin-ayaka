from typing_extensions import ParamSpec
from typing import TypeVar

T = TypeVar("T")

class A:
    ...
    
class YYY:
    def set(self, data: T):
        self.data = data
        return data


d = YYY()
ddd = d.set(A())
dd = d.data
