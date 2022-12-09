from pydantic import Field
from ayaka import AyakaApp, AyakaInput, AyakaCache

app = AyakaApp("星际旅行")
app.help = "xing ji lv xing"


# 启动应用
app.set_start_cmds("星际旅行", "travel")

# 装饰器的顺序没有强制要求，随便写


# 关闭应用
@app.on_state()
@app.on_deep_all()
@app.on_cmd("退出", "exit")
async def exit_app():
    await app.close()


# 注册各种行动
@app.on_cmd("drink")
@app.on_state("地球")
async def drink():
    '''喝水'''
    await app.send("喝水")


@app.on_state("月球")
@app.on_cmd("drink")
async def drink():
    '''喝土'''
    await app.send("喝土")


@app.on_deep_all()
@app.on_cmd("drink")
@app.on_state("太阳")
async def drink():
    '''喝太阳风'''
    await app.send("喝太阳风")


@app.on_cmd("drink")
@app.on_state(["太阳", "奶茶店"])
async def drink():
    '''喝奶茶'''
    await app.send("喝了一口3000度的奶茶")


class UserInput(AyakaInput):
    where: str = Field(description="你要去的地方")


@app.on_deep_all()
@app.on_state()
@app.on_cmd("move")
async def move(userinput: UserInput):
    '''移动'''
    await app.set_state(userinput.where)
    await app.send(f"前往 {userinput.where}")


@app.on_cmd("hi")
@app.on_deep_all()
@app.on_state()
async def say_hi():
    '''打招呼'''
    await app.send(f"hi I'm in {app.state.keys[2:]}")


class Cache(AyakaCache):
    ticket: int = 0


@app.on_state(["太阳", "售票处"])
@app.on_cmd("buy", "买票")
async def buy_ticket(cache: Cache):
    '''买门票'''
    cache.ticket += 1
    await app.send("耀斑表演门票+1")


@app.on_deep_all()
@app.on_state("太阳")
@app.on_cmd("watch", "看表演")
async def watch(cache: Cache):
    '''看表演'''
    if cache.ticket <= 0:
        await app.send("先去售票处买票！")
    else:
        cache.ticket -= 1
        await app.send("10分甚至9分的好看")


@app.on_state(["太阳", "奶茶店"])
async def handle():
    '''令人震惊的事实'''
    await app.send("你发现这里只卖热饮")
