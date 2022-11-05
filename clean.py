import os
import shlex
import nonebot

nonebot.init()
driver = nonebot.get_driver()

# 清理可能已经卡死的上一次的端口
port = driver.config.port
print(port)

# win10使用
result = os.popen(f'netstat -aon|findstr "{port}"')
info = result.read()
if not info:
    print("端口畅通")
else:
    print(info)
    lines = info.strip().split("\n")
    pids = set(shlex.split(line)[-1] for line in lines)
    input(f"{pids} kill?")

    for pid in pids:
        result = os.popen(f"taskkill -pid {pid} -f")
        print(result.read())
