from ayaka.driver import BOT_TYPE

# 仅nonebot可用
if BOT_TYPE == "nonebot":
    from . import cqhttp, terminal
