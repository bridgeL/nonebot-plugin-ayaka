from ayaka import AyakaApp

app = AyakaApp("星际旅行")
app.help = "xing ji lv xing"

# 状态
st_menu = app.get_state()
st_earth = app.get_state("地球")
st_moon = app.get_state("月球")
st_sun = app.get_state("太阳")

# 全部
all = app.on_deep_all()

# 星球
earth = app.on_state(st_earth)
moon = app.on_state(st_moon)
sun = app.on_state(st_sun)
menu = app.on_state(st_menu)

# 动作
hi = app.on_cmd("hi", "你好")
hit = app.on_cmd("hit", "打")
jump = app.on_cmd("jump", "跳")
drink = app.on_cmd("drink", "喝")
move = app.on_cmd("move", "移动")
stop = app.on_cmd("退出", "exit")


# 启动应用
app.set_start_cmds("星际旅行")


@all
@stop
@menu
async def exit_app():
    '''退出应用'''
    if app.state <= st_menu:
        await app.close()
    else:
        await app.back()


@all
@menu
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
    await app.send("你感觉肚子暖洋洋的")


@menu
@all
@move
async def handle():
    '''去其他地方转转'''
    names = [str(arg) for arg in app.args]
    state = app.get_state(*names)
    await app.goto(state)
    await app.send(f"你动身前往{state}")


# 补充

@app.on_state(["太阳", "奶茶店"])
@drink
async def handle():
    '''热乎的'''
    await app.send("喝了一口3000度的奶茶")


# 补充2

@app.on_state(["太阳", "售票处"])
@app.on_cmd("buy")
async def handle():
    '''买门票'''
    ctrl = app.cache.chain("ticket")
    ctrl.set(ctrl.get(0) + 1)
    await app.send("耀斑表演门票+1")


@all
@sun
@app.on_cmd("watch")
async def handle():
    '''去现场'''
    ctrl = app.cache.chain("ticket")
    ticket = ctrl.get(0)
    if ticket > 0:
        ctrl.set(ticket - 1)
        await app.send("耀斑表演门票-1")
        await app.goto("太阳", "耀斑表演")
        await app.send("10分甚至9分的好看")
    else:
        await app.send("你还没买票")


# 补充3
@app.on_state(["太阳", "耀斑表演"])
async def handle():
    '''令人震惊的事实'''
    await app.send("你发现你的奶茶比表演项目还烫")
