
```python
'''
    背包
'''
from ayaka import *

app = AyakaApp('背包')
app.help = "[#bag]"


@app.on_command(['bag', '背包'], super=True)
async def bag():
    uid = app.event.user_id
    name = app.event.sender.card
    money = get_money(app, uid)

    ans = f"[{name}] 当前有 {money}金"
    await app.send(ans)


def get_money(_app: AyakaApp, uid: int) -> int:
    sa = _app.storage.accessor(uid, "money")
    money = sa.get()
    if money is None:
        # 初始100金
        sa.set(100)
        return 100
    return money
```

无论当前是否有交互式应用运行，都不影响该插件的`bag`回调的命令触发，这样可以便于玩家快速查询背包，而无需中断当前正在进行的游戏

这一特性的具体实现可以查看 `ayaka/core/deal.py:deal_device()`


# 上下文切换
触发回调时，插件里的app会自动切换到对应`机器人`对应`设备`的对应`应用`

所有回调也无需使用参数，所有参数都已经写入到app身上了

可以使用的参数有：

|名称|类型|功能|
|-|-|-|
| app.state   | `str`          | 应用当前的状态 |
| app.valid   | `bool`         | 应用在当前设备 可启用/已禁用 |
| app.bot     | `Bot` | 用于发送各种命令和消息，来自于`nonebot.adapters.onebot.v11` |
| app.device  | `AyakaDevice`  | 保存了当前设备的所有应用 |
| app.event   | `MessageEvent` | 当前消息事件 |
| app.message | `Message`      | 删除了命令后剩下的消息部分，例如 "#exit你好" => "你好" |
| app.args    | `List[str]`    | `删除了命令后剩下的消息部分` 按照 `shell分割规则` 得到的 `参数列表` |
| app.cmd     | `str`          | 对于注册了多个命令的回调，告知该回调，本次响应是针对哪个命令 |
| app.cache   | `Cache`        | 为本应用提供的缓存，使用`app.cache.\<name>`即可存取数据 |


得益于上下文机制，发送消息时，如下两种发送方式都是允许的

- `await app.bot.send(app.event, "我在你上面")`
- `await app.send("你给我下来")`

# 缓存与固存
使用`app.cache`和`app.storage`实现，各个`机器人`各个`设备`各个`应用`间的存储是相互隔离的

## 缓存读写

```python
# 通过魔术方法 __setattr__ 实现

...

app.cache.users = users

...

users = app.cache.users

...

```

