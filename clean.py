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
    pid = shlex.split(info)[-1]
    print(info, pid)
    input("确认kill? ")

    result = os.popen(f"taskkill -pid {pid} -f")
    print(result.read())
