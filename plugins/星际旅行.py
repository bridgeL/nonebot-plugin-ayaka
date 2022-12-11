from pydantic import Field
from ayaka import AyakaApp, AyakaInput, AyakaCache, AyakaUserDB, AyakaConfig

app = AyakaApp("星际旅行")
app.help = "xing ji lv xing"

# 启动应用
app.set_start_cmds("星际旅行", "travel")
# 关闭应用
app.set_close_cmds("退出", "exit")


# 装饰器的顺序没有强制要求，随便写
# 注册各种行动
@app.on_state("地球")
@app.on_cmd("drink")
async def drink():
    '''喝水'''
    await app.send("喝水")


@app.on_state("月球")
@app.on_cmd("drink")
async def drink():
    '''喝土'''
    await app.send("喝土")


@app.on_state("太阳")
@app.on_deep_all()
@app.on_cmd("drink")
async def drink():
    '''喝太阳风'''
    await app.send("喝太阳风")


class UserInput(AyakaInput):
    where: str = Field(description="你要去的地方")


@app.on_state()
@app.on_deep_all()
@app.on_cmd("move")
async def move(userinput: UserInput):
    '''移动'''
    await app.set_state(userinput.where)
    await app.send(f"前往 {userinput.where}")


@app.on_state()
@app.on_deep_all()
@app.on_cmd("hi")
async def say_hi():
    '''打招呼'''
    await app.send(f"hi I'm in {app.state[2:]}")


@app.on_state(["太阳", "奶茶店"])
@app.on_cmd("drink")
async def drink():
    '''喝奶茶'''
    await app.send("喝了一口3000度的奶茶")


class Cache(AyakaCache):
    ticket: int = 0


@app.on_state(["太阳", "售票处"])
@app.on_cmd("buy", "买票")
async def buy_ticket(cache: Cache):
    '''买门票'''
    cache.ticket += 1
    await app.send("耀斑表演门票+1")


@app.on_state("太阳")
@app.on_deep_all()
@app.on_cmd("watch", "看表演")
async def watch(cache: Cache):
    '''看表演'''
    if cache.ticket <= 0:
        await app.send("先去售票处买票！")
    else:
        cache.ticket -= 1
        await app.send("10分甚至9分的好看")


@app.on_state(["太阳", "奶茶店"])
@app.on_text()
async def handle():
    '''令人震惊的事实'''
    await app.send("你发现这里只卖热饮")


class Data(AyakaUserDB):
    __table_name__ = "gold"
    gold_number: int = 0


class Config(AyakaConfig):
    __app_name__ = "gold"
    each_number: int = 1


config = Config()


@app.on_state(["太阳", "森林公园"])
@app.on_cmd("pick")
async def get_gold(data: Data):
    '''捡金子'''
    data.gold_number += config.each_number
    data.save()
    await app.send(f"喜加一 {data.gold_number}")


class UserInput2(AyakaInput):
    number: int = Field(description="一次捡起的金块数量")


@app.on_state(["太阳", "森林公园"])
@app.on_cmd("change")
async def change_gold_number(userinput: UserInput2):
    '''修改捡金子配置'''
    config.each_number = userinput.number
    await app.send("修改成功")
