# Ayaka 0.3.0
针对Nonebot2框架 Onebot_v11协议的文字游戏开发辅助插件

<img src="https://img.shields.io/badge/python-3.8%2B-blue">

<b>注意：由于更新pypi的readme.md需要占用版本号，因此其readme.md可能不是最新的，强烈建议读者前往[github仓库](https://github.com/bridgeL/nonebot-plugin-ayaka)以获取最新版本的帮助</b>


# 更新记录

<details>
<summary>更新记录</summary>

版本|备注
-|-
0.3.0 | 借助contextvar内置模块，全部重写了之间的代码，现在它们被合并为一个单文件，并能实现ayaka插件先前提供的所有功能，但不幸的是，其无法兼容0.2.x的ayaka插件，需要代码迁移


</details>

# 安装
`pip install nonebot-plugin-ayaka` 

在 `bot.py` 中 写入 `nonebot.load_plugin("ayaka")`

# 快速了解

通过ayaka插件，二次封装nonebot2提供的api，提供专用api，便于其他文字游戏插件的编写

## 特性

群聊

## 插件编写范例

```python
'''
    具有状态机的复读模块
'''
from ayaka import *

app = AyakaApp("echo")

# ayaka内置帮助插件，用户可通过#help命令展示app.help
app.help = "复读只因"

# 另一种写法
# 当app处于run状态时，用户发送help指令将返回对应的提示 
app.help = {
    "":"复读只因",
    "run":"echo正在运行~\n使用[#exit] 退出"
}


@app.on_command("echo")
async def app_entrance():
    # 运行该应用
    await app.start()

    # 用户可以为该复读提供一个前缀，例如 "无穷小亮说："
    if app.args:
        app.cache.prefix = str(app.args[0])

    await app.send(info)


# 当app为run状态时响应
@app.on_state_command(["exit", "退出"])
async def app_exit():
    # 关闭该应用
    f, info = app.close()
    await app.send(info)


# 当app为run状态时响应
@app.on_state_text()
async def repeat():
    prefix = app.cache.prefix
    if prefix is None:
        prefix = ""
    await app.send(prefix + str(app.message))


# 桌面模式下执行
@app.on_text()
async def hi():
    if str(app.message).startswith("hello"):
        await app.send(app.message)
```

