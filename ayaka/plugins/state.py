'''
当前状态
'''
from .. import *

app = AyakaApp('状态查询')
app.help = '''状态查询 [#state]'''


@app.on_command(['state', '状态'], super=True)
async def show_state():
    _app = app.device.running_app
    if _app:
        await app.send(f"设备正在运行应用[{_app.name} | {_app.state}]")
    else:
        await app.send(f"设备正在处于桌面模式")

