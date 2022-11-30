from ayaka.config import ayaka_root_config

# 仅nonebot可用
if ayaka_root_config.bot_type == "nonebot":
    from . import cqhttp, terminal
