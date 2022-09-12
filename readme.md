# Ayaka
针对Nonebot2框架 Onebot_v11协议的文字游戏开发辅助插件

<img src="https://img.shields.io/badge/python-3.8%2B-blue">

# 安装
`pip install nonebot-plugin-ayaka` 

在 `bot.py` 中 写入 nonebot.load_plugin("ayaka")

# 快速了解

通过ayaka插件，二次封装nonebot2提供的api，提供专用api，便于其他文字游戏插件的编写

```python
# ayaka.lazy 提供的类和方法
from .model import AyakaBot, AyakaDevice, AyakaApp, Storage, Cache, Trigger, create_path, create_file, beauty_save, logger
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageEvent, Message, MessageSegment
```

## ayaka的优势

### 状态机，命令隔离

与nonebot2自带的state相比，ayaka更专注于提供长期的、针对一个群聊整体的、而非仅一个事件处理流程的状态机

而且ayaka能够<b>管理多个不同的文字游戏</b>，他们之间的命令被ayaka在后台隐式地实现隔离，开发者无需担心命令冲突

并且，当同一个文字游戏处于不同的游戏状态时，其命令空间亦是隔离的

### 有限、简练的参数

文字游戏插件所需要的数据高度类似，仅需使用有限、简练的参数即可，无需使用依赖注入，<b>ayaka激进地取消了回调的参数表</b>

ayaka将各类参数引用直接放在app身上，节约了开发者反复编写同一份参数表的时间

ayaka提供的参数[如下](#上下文切换)

### 缓存、固存

自带[缓存与固存](#缓存与固存)，无需安装额外插件

### 无需关注插件导入顺序，无需使用require

### 帮助命令
只需设置app.help

### 不止于文字游戏

如果其他插件想要利用ayaka实现缓存、固存、状态机管理、命令隔离，只需遵循ayaka插件的编写规范即可使用


# 插件编写范例

```python
'''
    具有状态机的复读模块
'''
from ayaka.lazy import *

app = AyakaApp("echo")

# ayaka内置帮助插件，用户可通过#help命令展示app.help
app.help = "复读只因"

# 另一种写法
# 当app处于run状态时，用户发送help指令将返回对应的提示 
app.help = {
    "介绍":"复读只因",
    "run":"echo正在运行~\n使用[#exit] 退出"
}


@app.on_command("echo")
async def app_entrance():
    # 运行该应用
    # 令其进入run状态
    f, info = app.start("run")

    # 用户可以为该复读提供一个前缀，例如 "无穷小亮说："
    args = app.args
    if args:
        app.cache.prefix = args[0]

    await app.send(info)


# 当app为run状态时响应
@app.on_command(["exit", "退出"], "run")
async def app_exit():
    # 关闭该应用
    f, info = app.close()
    await app.send(info)


# 当app为run状态时响应
@app.on_text("run")
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

## 注册命令监听
`@app.on_command(cmds, states=None, super=False)`

指示AyakaApp将一个或多个`命令监听`注册到指定的一个或多个状态下

注意：写入的单项字符串会自动转换为数组，例如 "echo" => ["echo"]，因此当开发者仅需要指定一个命令或状态时，无需多敲一对`[]`

如果states缺省，则默认将该命令注册到[桌面模式](#桌面模式)

## 注册消息监听
`@app.on_text(states=None, super=False)`

指示AyakaApp将`消息监听`注册到指定的一个或多个状态下

如果states缺省，则默认将该消息监听注册到[桌面模式](#桌面模式)（相当于 [即问即答式应用](#即问即答式应用) 的回调）

# 机器人、设备、应用
`Ayaka`将为每一个建立了ws连接的`Bot`创建一个对应的`AyakaBot`

每一个`AyakaBot`内部保存了该机器人所管理的所有群聊和私聊，并将它们视为设备`AyakaDevice`进行管理

而依附于`ayaka`的文字游戏插件是安装到各个设备上的应用`AyakaApp`

同一时刻同一设备只能运行一个应用，各个应用的命令相互隔离，同一应用内不同状态时的命令相互隔离

应用分为两类：交互式应用，即问即答式应用

## 交互式应用

- 文字游戏（需要状态机支持，用户的历史输入会影响当前的输出）

桌面模式下，可以运行交互式应用的启动命令，随后ayaka退出桌面模式，进入仅运行该交互式应用的独占模式

## 即问即答式应用

即问即答时应用仅在桌面模式下运行

- 计算器（无状态，用户的历史输入对当前的输出没有任何影响）

不过，开发者在编写插件时，使用统一的`AyakaApp`来声明即可，无需特殊关注

# 桌面模式
如果没有任何应用在运行，则设备进入桌面模式

此时，可以发送命令`开启`交互式应用，可以发送命令`执行`即问即答式应用

开启交互式应用后，设备将只对交互式应用里注册的命令做出响应

不过，为了满足特殊需要，注册command或text时可设置`super=True`，则该回调可以优先于任何交互式应用执行

例如，背包查询插件 `ayaka/plugins/bag.py`，无论当前是否有交互式应用运行，都不影响该插件的回调正常触发，这样可以便于玩家快速查询背包，而无需中断当前正在进行的游戏

这一特性的具体实现可以查看 `ayaka/device.py:deal_device()`


# 上下文切换
触发回调时，插件里的app会自动切换到对应`机器人`对应`设备`的对应`应用`

所有回调也无需使用参数，所有参数都已经写入到app身上了

可以使用的参数有：

| 名称        | 类型           | 功能                                                                                                                                           |
| ----------- | -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| app.state   | `str`          | 应用当前的状态                                                                                                                                 |
| app.abot    | `AyakaBot`     | 保存了当前机器人的所有设备                                                                                                                     |
| app.bot     | `OneBot`       | 用于发送各种命令和消息                                                                                                                         |
| app.device  | `AyakaDevice`  | 保存了当前设备的所有应用                                                                                                                       |
| app.event   | `MessageEvent` | 当前消息事件                                                                                                                                   |
| app.message | `Message`      | 删除了命令后剩下的消息部分，例如 "#exit你好" => "你好"                                                                                         |
| app.args    | `List[str]`    | 删除了命令后剩下的消息部分按照shell分割规则得到的参数列表                                                                                      |
| app.cmd     | `str`          | 对于注册了多个命令的回调，告知该回调，本次响应是针对哪个命令                                                                                   |
| app.cache   | `Cache`        | 为本应用提供的缓存，使用app.cache.\<name>即可存取数据                                                                                          |
| app.storage | `Storage`      | 为本应用提供的本地存取，使用app.storage.accessor创建一个访问器，随后get、set即可，保存地址为 data/storage/<bot_id>/<device_id>/<app_name>.json |

得益于上下文机制，发送消息时，如下两种发送方式都是允许的

- `await app.bot.send(app.event, "我在你上面")`
- `await app.send("你给我下来")`

# 缓存与固存
使用`app.cache`和`app.storage`实现，各个机器人各个设备各个应用间的存储是相互隔离的

## 缓存读写

```python
# 通过魔术方法 __setattr__ 实现

...

app.cache.users = users

...

users = app.cache.users

...

```

## 固存访问器

```python
sa = app.storage.accessor("father", "name")
sa.set("周朴园")
sa = app.storage.accessor("father", "age")
sa.set(42)
sa = app.storage.accessor("mother")
sa.set("周侍萍")
```

如上代码对应的现实存储为：

打开data/storage/<bot_id>/<device_id>/<app_name>.json文件

```json
{
    "father":{
        "name":"周朴园",
        "age":42
    },
    "mother": "周侍萍"
}
```

# 更新计划
`app.storage`可以考虑修改为sqlite实现，而不再使用本地的json文件
