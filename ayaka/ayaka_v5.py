'''下一代ayaka命令状态设计，对接onebot v11'''
from typing import List

from .driver import MessageSegment, Message

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
