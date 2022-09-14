'''
管理应用 启用/禁用
'''
from .. import *

app = AyakaApp('应用管理', no_storage=True)
app.help = '''管理应用 启用/禁用
[#valid <应用名>] 启用应用
[#invalid <应用名>] 禁用应用'''

def check(event:MessageEvent):
    if isinstance(event, GroupMessageEvent):
        return event.sender.role in ["admin", "owner"]
    return True    


@app.on_command(['valid', '启用', '开启'])
async def valid():
    if not check(app.event):
        await app.send("您没有操作权限")
        return

    if not app.args:
        await app.send("您没有输入要开启的应用名")
        return
        
    app_name = app.args[0]
    _app = app.device.get_app(app_name)
    if not _app:
        await app.send(f"没有找到应用[{app_name}]")
        return

    _app.valid = True
    await app.send(f"已启用应用[{app_name}]")

@app.on_command(['invalid', '禁用', '关闭'])
async def invalid():
    if not check(app.event):
        await app.send("您没有操作权限")
        return

    if not app.args:
        await app.send("您没有输入要禁用的应用名")
        return
        
    app_name = app.args[0]
    _app = app.device.get_app(app_name)
    if not _app:
        await app.send(f"没有找到应用[{app_name}]")
        return

    _app.valid = False
    await app.send(f"已禁用应用[{app_name}]")

