# Ayaka 0.3.1
针对Nonebot2框架 Onebot_v11协议的文字游戏开发辅助插件

<img src="https://img.shields.io/badge/python-3.8%2B-blue">

<b>注意：由于更新pypi的readme.md需要占用版本号，因此其readme.md可能不是最新的，强烈建议读者前往[github仓库](https://github.com/bridgeL/nonebot-plugin-ayaka)以获取最新版本的帮助</b>


# 更新记录

<details>
<summary>更新记录</summary>

| 版本  | 备注 |
| - | - |
| 0.3.0 | 借助contextvar内置模块，全部重写了之间的代码，现在它们被合并为一个单文件，并能实现ayaka插件先前提供的所有功能，但不幸的是，其无法兼容0.2.x的ayaka插件，需要代码迁移 |
| 0.3.1 | 规定了应用启动后的默认初始状态为 init |


</details>

# 安装
`pip install nonebot-plugin-ayaka` 

无需修改`bot.py`，在ayaka衍生插件里引用即可，`from ayaka import AyakaApp`

但是ayaka衍生插件需要nonebot来加载

# 快速了解

通过ayaka插件，二次封装nonebot2提供的api，提供专用api，便于其他文字游戏插件的编写

## 基本特性
- 状态机
- 命令隔离
- 数据隔离

## 插件编写范例 echo

```python
'''
    具有状态机的复读模块
'''
from ayaka import AyakaApp

app = AyakaApp("echo")

# ayaka内置帮助插件，用户可通过#help命令展示app.help
app.help = '''复读只因
特殊命令一览：
- reverse 开始说反话
- back 停止说反话
- exit 退出
'''

# 另一种写法
app.help = {
    "init": "复读只因\n特殊命令一览：\n- reverse 开始说反话\n- exit 退出",
    "reverse": "说反话模式\n- back 停止说反话"
}


# 桌面状态下
@app.on_command("echo")
async def app_entrance():
    if app.args:
        await app.send(" ".join(str(arg) for arg in app.args))
        return

    # 没有输入参数则运行该应用
    await app.start()


# app运行后，进入初始状态(state = "init")

# 正常复读
@app.on_state_text()
async def repeat():
    await app.send(app.message)


# 任意状态均可直接退出
@app.on_state_command(["exit", "退出"], "*")
async def app_exit():
    await app.close()


# 通过命令，跳转到reverse状态
@app.on_state_command(["rev", "reverse", "话反说", "反", "说反话"])
async def start_rev():
    app.set_state("reverse")
    await app.send("开始说反话")


# 反向复读
@app.on_state_text("reverse")
async def reverse_echo():
    msg = str(app.message)
    msg = "".join(s for s in reversed(msg))
    await app.send(msg)


# 通过命令，跳转回初始状态
@app.on_state_command("back", "reverse")
async def back():
    app.set_state()
    await app.send("话反说止停")

```


## 插件编写范例 hello world

```python

'''
    ayaka可以帮助你实现命令隔离
'''
from ayaka import AyakaApp

app = AyakaApp("hello-world")

# 你可以不写帮助
# app.help


# 桌面状态下
@app.on_command("hw")
async def app_entrance():
    await app.start()
    # app运行后，进入指定状态(state = "world")
    app.set_state("world")


# 只有world状态可以退出，其他状态运行该指令均为返回world状态
@app.on_state_command(["exit", "退出"], "*")
async def app_exit():
    if app.state == "world":
        await app.close()
    else:
        app.set_state("world")
        await app.send("跳转到 world")


# 对世界、月亮和太阳打个招呼
@app.on_state_command("hi", ["world", "moon", "sun"])
async def hello():
    await app.send(f"hello,{app.state}!")


# 对世界、月亮和太阳来个大比兜
@app.on_state_command("hit", "world")
async def hit():
    await app.send("earthquake")


@app.on_state_command("hit", "moon")
async def hit():
    await app.send("moon fall")


@app.on_state_command("hit", "sun")
async def hit():
    await app.send("bag bang!")


# 跳转状态
@app.on_state_command("jump", "*")
async def jump_to_somewhere():
    if not app.args:
        await app.send("没有参数！")
    else:
        next_state = str(app.args[0])
        app.set_state(next_state)
        await app.send(f"跳转到 [{next_state}]")
```

## 插件编写范例 a plus b

```python
'''
    a + b 各群聊间、各插件间，数据独立，互不影响
'''
from ayaka import AyakaApp

app = AyakaApp("a-plus-b")


@app.on_command("set_a")
async def set_a():
    app.cache.a = int(str(app.args[0])) if app.args else 0
    await app.send(app.cache.a)


@app.on_command("set_b")
async def set_b():
    app.cache.b = int(str(app.args[0])) if app.args else 0
    await app.send(app.cache.b)


@app.on_command("calc")
async def calc():
    a = app.cache.a or 0
    b = app.cache.b or 0
    await app.send(str(a+b))
```

# 更多特性

## 定时器 Timer

注意，定时器触发回调时，由于缺乏消息激励源，app的大部分属性(bot、group、event、valid、cache、user_name等)将无法正确访问到，并且无法使用app.send方法，需要使用专用的t_send方法

```python
'''
    整点报时
'''
from ayaka import AyakaApp

app = AyakaApp("整点报时")


@app.on_interval(60, s=0)
async def every_minute():
    await app.t_send(bot_id=2317709898, group_id=666214666, message="小乐")


@app.on_interval(3600, m=0, s=0)
async def every_hour():
    await app.t_send(bot_id=2317709898, group_id=666214666, message="大乐")


@app.on_everyday(h=23, m=59, s=59)
async def every_day():
    await app.t_send(bot_id=2317709898, group_id=666214666, message="呃呃呃一天要结束了")

```

## 截图 playwright

注意，win平台使用playwright + nb时需要关闭fastapi的reload功能

```python

'''
    can can baidu
'''

from pathlib import Path
from ayaka import get_new_page, AyakaApp, MessageSegment

app = AyakaApp("看看baidu")


@app.on_command("ccb")
async def _():
    async with get_new_page() as p:
        await p.goto("http://www.baidu.com", wait_until="networkidle")
        path = Path("test.png").absolute()
        await p.screenshot(path=path)
    image = MessageSegment.image(path)
    await app.send(image)

```

# 未来计划
提供aiosqlite数据库支持
