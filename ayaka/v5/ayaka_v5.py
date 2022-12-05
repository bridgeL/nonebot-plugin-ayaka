'''下一代ayaka命令状态设计，对接onebot v11'''
from typing import List

from ..driver import MessageSegment, Message

# 争取做到类似click包的效果
# click 对应的是分离str
# 而ayaka_v5对应的是MessageSegment


# 分离函数单独写
def div(msg: Message) -> List[MessageSegment]:
    pass


'''
触发条件1 参数1 操作1
    (前提:触发条件1) 触发条件2 参数1 参数2 操作2
    (前提:没有其他进一步触发) 参数1 操作3
    
触发条件1 操作1
触发条件1 触发条件2 操作2
触发条件1 无进一步触发 操作3

state, command

    state, command
'''


class AyakaState:
    def __init__(self) -> None:
        self.keys = []

    def __add__(self, d):
        ...


state = "根.应用名.一级菜单项.二级菜单项"

app = {}

command = "测试"

app.entrance = [command]
# 设置入口
# 触发指令时开启应用并发送提示：xx已开启

root_state = AyakaState()
# 根

# no state
@root_state.command()
@root_state.text()
async def _():
    ...

current_state = app.state
# 应用名
# 应用名.一级菜单项
# 应用名.一级菜单项.二级菜单项

state = app.create_state("sdf", "最好按照python变量的格式要求来命名状态")
# AyakaState(app.name, ...)
# 根.应用名.sdf.最好按照python变量的格式要求来命名状态

# 进入该状态时执行回调
@state.entrance
async def _():
    ...
    
# 退出该状态时执行回调
@state.exit
async def _():
    ...
    
# 该状态下收到命令时执行回调
@state.command(deep=0)
# 不监听子状态的命令
async def _():
    ...
    
# 该状态下收到消息时执行回调
@state.text(deep="any")
# 监听任意层数子状态的消息
async def _():
    app.goto("state1", "state2", base = "current" or "plugin_name" or "root")
    # base current
    # 先进入state1，执行state1.entrance回调
    # 再进入state2，执行state2.entrance回调
    # 注意，需要设法保证，在任意回调注册顺序下，这个机制都是正确进行的
    # base root
    # 先判断进出关系
    # 可能是先退出state3，执行state3.exit回调后再执行各种entrance的回调
    # app.group.state.goto()
    app.back()
    # 返回上一层，最多可返回到 根
    await app.exit()
    # 返回到根，并发送消息通知：xx已关闭
    # app.group.state.goto()
