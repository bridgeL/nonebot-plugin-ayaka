from .. import *

app = AyakaApp('重启')
app.help = '''[#reboot] 重启当前设备'''


@app.on_command(['reboot', '重启'], super=True)
async def reboot():
    app.device.reboot()
