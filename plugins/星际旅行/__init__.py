from ayaka import AyakaApp

app = AyakaApp("星际旅行")
app.help = "xing ji lv xing"


# 启动应用
@app.on.idle()
@app.on.command("星际旅行")
async def app_start():
    '''打开应用'''
    # 设置初始状态为地球
    await app.start("地球")


# 星球
earth = app.on.state("地球")
moon = app.on.state("月球", "月亮")
sun = app.on.state("太阳")
all = app.on.state("*")

# 动作
hi = app.on.command("hi", "你好")
hit = app.on.command("hit", "打")
jump = app.on.command("jump", "跳")
drink = app.on.command("drink", "喝")


@all
@hi
async def handle():
    '''打个招呼'''
    await app.send(f"你好, {app.state}!")


@earth
@jump
async def handle():
    '''跳一跳'''
    await app.send("一跳两米高")


@earth
@hit
async def handle():
    '''打一打'''
    await app.send("你全力一击，制造了大地震")


@moon
@jump
async def handle():
    '''跳一跳'''
    await app.send("你离开了月球...永远的...")


@sun
@drink
async def handle():
    '''drink 1 drink'''
    await app.send("嘿！像是一团火球进了胃")


@all
@app.on.command("goto")
async def handle():
    '''去其他地方转转'''
    name = str(app.arg)
    app.state = name
    await app.send(f"你动身前往{name}")


# 关闭应用
@all
@app.on.command("exit", "quit", "退出")
async def handle():
    '''退出'''
    await app.close()


# 补充1
@app.on.state("太阳.奶茶店")
@drink
async def handle():
    '''热乎的'''
    await app.send("喝了一口3000度的奶茶")


# 补充2
@app.on.state("太阳.售票处")
@app.on.command("buy")
async def handle():
    '''买门票'''
    app.cache.ticket = 1
    await app.send("耀斑表演门票+1")


@app.on.state("太阳")
@app.on.command("watch", "去现场")
async def handle():
    '''去现场'''
    if app.cache.ticket:
        app.cache.ticket -= 1
        await app.send("耀斑表演门票-1")
        app.state = "太阳.耀斑表演"
        await app.send("10分甚至9分的好看")
    else:
        await app.send("你还没买票")


# 补充3
@app.on.state("太阳.耀斑表演")
@app.on.text()
async def handle():
    '''令人震惊的事实'''
    await app.send("你发现你的奶茶比表演项目还烫")
