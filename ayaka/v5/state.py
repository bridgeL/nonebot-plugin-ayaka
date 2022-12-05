from typing import List, Literal, Union
from ayaka.driver import Message, MessageSegment



class AyakaApp:
    def __init__(self, name) -> None:
        self.name = name
        self.group = group



app = AyakaApp("测试")
s0 = app.get_state("test")
s1 = app.get_state("ok", from_="root")
print(s0, s1)

print(app.state)
app.state = ["test", "ok"]
print(app.state)
app.state = s0
print(app.state)

print(root_state.dict())
