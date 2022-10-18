# Ayaka 0.3.5
针对Nonebot2框架 Onebot_v11协议的文字游戏开发辅助插件

<img src="https://img.shields.io/badge/python-3.8%2B-blue">

<b>注意：由于更新pypi的readme.md需要占用版本号，因此其readme.md可能不是最新的，强烈建议读者前往[github仓库](https://github.com/bridgeL/nonebot-plugin-ayaka)以获取最新版本的帮助</b>


# 更新记录

<details>
<summary>更新记录</summary>

## 0.3.0 
借助contextvar内置模块，全部重写了之间的代码，现在它们被合并为一个单文件，并能实现ayaka插件先前提供的所有功能，但不幸的是，其无法兼容0.2.x的ayaka插件，需要代码迁移 
## 0.3.1 
规定了应用启动后的默认初始状态为 init 
## 0.3.2 
增加了较为完善的注释 
## 0.3.3 
在本文档中更新了部分帮助

</details>

# 安装
`pip install nonebot-plugin-ayaka` 

无需修改`bot.py`，在ayaka衍生插件里引用即可，`from ayaka import AyakaApp`

**但是ayaka衍生插件需要nonebot来加载**

## 配置

推荐配置（非强制要求）
```
COMMAND_START=["#"]
COMMAND_SEP=[" "]
```

# 快速了解

通过ayaka插件，二次封装nonebot2提供的api，提供专用api，便于其他文字游戏插件的编写

基于ayaka的衍生插件库 https://github.com/bridgeL/ayaka_plugins

基于ayaka的小游戏合集 https://github.com/bridgeL/nonebot-plugin-ayaka-games

基于ayaka的谁是卧底小游戏 https://github.com/bridgeL/nonebot-plugin-ayaka-who-is-suspect

## 基本特性
- 状态机
- 命令隔离
- 数据隔离

## 代码速看

```python
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
    await app.send("big bang!")


# 跳转状态
@app.on_state_command("jump", "*")
async def jump_to_somewhere():
    if not app.arg:
        await app.send("没有参数！")
    else:
        next_state = str(app.arg)
        app.set_state(next_state)
        await app.send(f"跳转到 [{next_state}]")
```

## app属性一览表
| 名称      | 类型                   | 功能                                           |
| --------- | ---------------------- | ---------------------------------------------- |
| intro     | `str`                  | 应用介绍（帮助dict中key为init所对应的value）   |
| help      | `str`                  | 当前应用在当前状态下的帮助                     |
| all_help  | `str`                  | 当前应用的所有帮助                             |
| state     | `bool`                 | 当前应用的状态                                 |
| valid     | `bool`                 | 应用在当前设备 是否被启用                      |
| bot       | `Bot`                  | 当前机器人                                     |
| group     | `AyakaGroup`           | 当前群组                                       |
| event     | `MessageEvent`         | 当前消息事件                                   |
| message   | `Message`              | 当前消息                                       |
| arg       | `Message`              | 删除了命令后剩下的消息部分                     |
| args      | `List[MessageSegment]` | 删除命令后，依照分隔符分割，并移除空数据       |
| cmd       | `str`                  | 本次响应是针对哪个命令                         |
| bot_id    | `int`                  | 当前机器人的qq号                               |
| group_id  | `int`                  | 当前群聊的群号                                 |
| user_id   | `int`                  | 当前消息的发送者的qq号                         |
| user_name | `str`                  | 当前消息的发送者的群名片或昵称（优先为群名片） |
| cache     | `AyakaCache`           | 为当前群组当前应用提供的独立缓存数据空间       |

## app方法一览表
| 名称             | 功能                                      |
| ---------------- | ----------------------------------------- |
| set_state        | 设置应用状态（在应用运行时可以设置）      |
| on_command       | 注册桌面模式下的命令回调                  |
| on_state_command | 注册应用运行时在不同状态下的命令回调      |
| on_text          | 注册桌面模式下的消息回调                  |
| on_state_text    | 注册应用运行时在不同状态下的消息回调      |
| on_everyday      | 每日定时触发回调（东8区）                 |
| on_interval      | 在指定的时间点后开始循环触发（东8区）     |
| add_listener     | 为该群组添加对 指定私聊 的监听            |
| remove_listener  | 移除该群组对 指定私聊/所有其他私聊 的监听 |

## ayaka 内置插件

ayaka内部已安装一份特殊的综合管理插件，它基于ayaka插件而实现

命令一览：
- 启用/permit
- 禁用/forbid
- 插件/plugin
- 状态/state
- 帮助/help
  
### 帮助
所有ayaka衍生插件只需要编写app.help，就可以在用户输入 `#help` 后获取该插件的帮助

# 例程代码

如何使用例程代码？

1. 你可以在nonebot工作目录的src/plugins中新建一个代码文件，手动复制代码进去，nonebot会在读到`bot.py`文件中的`nonebot.load_from_toml(...)`语句后导入该插件
2. 你也可以前往[ayaka衍生插件库](https://github.com/bridgeL/ayaka_plugins)，下载其中的example文件夹，放到nonebot工作目录下，然后在`bot.py`中添加`nonebot.load_plugin("example")`

## 插件编写范例 echo

```python
'''
    具有状态机的复读模块
'''
from ayaka import AyakaApp

app = AyakaApp("echo")

# 结合ayaka_master插件，用户可通过#help命令展示app.help
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
    # 输入参数则复读参数（无状态响应
    # > #echo hihi
    # < hihi
    if app.arg:
        await app.send(app.arg)
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
    await app.send("big bang!")


# 跳转状态
@app.on_state_command("jump", "*")
async def jump_to_somewhere():
    if not app.arg:
        await app.send("没有参数！")
    else:
        next_state = str(app.arg)
        app.set_state(next_state)
        await app.send(f"跳转到 [{next_state}]")
```

## 插件编写范例 a plus b

```python
'''
    a + b 
    
    各群聊间、各插件间，数据独立，互不影响；不需要自己再专门建个字典了
'''
from ayaka import AyakaApp

app = AyakaApp("a-plus-b")


@app.on_command("set_a")
async def set_a():
    app.cache.a = int(str(app.arg)) if app.arg else 0
    await app.send(app.cache.a)


@app.on_command("set_b")
async def set_b():
    app.cache.b = int(str(app.arg)) if app.arg else 0
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

## 自动分割消息

ayaka插件将会自动根据配置项中的分割符来分割消息，例如

```
#test a   b c
```

会在ayaka插件处理后变为

```python
@app.on_command("test")
async def _():
    # 此时app身上的如下属性值应该是：...
    app.cmd = "test"
    app.arg = "a   b c"
    app.args = ["a", "b", "c"]
```

# 未来计划
提供aiosqlite数据库支持
