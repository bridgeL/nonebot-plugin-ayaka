from ayaka.lazy import *

app = AyakaApp("echo")
app.help = "复读只因"


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