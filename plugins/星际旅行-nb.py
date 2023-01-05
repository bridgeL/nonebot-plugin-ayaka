# ---------- 1 ----------
from ayaka import AyakaBox
from nonebot import on_command

box = AyakaBox("星际旅行-nb")
box.help = "xing ji lv xing"

# 启动应用
m1 = on_command("星际旅行-nb", aliases={"travel-nb"}, rule=box.rule())
@m1.handle()
async def start():
    await box.start()
    
# 关闭应用
m2 = on_command("退出", aliases={"exit"}, rule=box.rule(states="*"))
@m2.handle()
async def close():
    await box.close()

# ---------- 2 ----------
m3 = on_command("move", rule=box.rule(states="*"))
@m3.handle()
async def move():
    '''移动'''
    arg = str(box.arg)
    await box.set_state(arg)
    await m3.send(f"前往 {arg}")
    
# ---------- 3 ----------
m4 = on_command("hi", rule=box.rule(states=["地球", "月球", "太阳"]))
@m4.handle()
async def say_hi():
    '''打招呼'''
    await m4.send(f"你好，{box.state}！")

# ---------- 4 ----------
# 相同命令，不同行为
m5 = on_command("drink", rule=box.rule(states=["地球", "月球"]))
@m5.handle()
async def drink():
    '''喝水'''
    await m5.send("喝水")

m6 = on_command("drink", rule=box.rule(states="太阳"))
@m6.handle()
async def drink():
    '''喝太阳风'''
    await m6.send("喝太阳风")

# ---------- 5 ----------
from ayaka import BaseModel

class Cache(BaseModel):
    ticket:int = 0

m7 = on_command("buy", aliases={"买票"}, rule=box.rule(states="售票处"))
@m7.handle()
async def buy_ticket():
    '''买门票'''
    cache = box.get_data(Cache)
    cache.ticket += 1
    await m7.send("耀斑表演门票+1")

m8 = on_command("watch", aliases={"看表演"}, rule=box.rule(states="*"))
@m8.handle()
async def watch():
    '''看表演'''
    cache = box.get_data(Cache)
    if cache.ticket <= 0:
        await m8.send("先去售票处买票！")
    else:
        cache.ticket -= 1
        await m8.send("门票-1")
        await m8.send("10分甚至9分的好看")

# ---------- 6 ----------
from nonebot import on_message

m9 = on_message(rule=box.rule(states="火星"))
@m9.handle()
async def handle():
    '''令人震惊的事实'''
    await m9.send("你火星了")

# ---------- 7 ----------
from ayaka import AyakaConfig, slow_load_config

class Cache2(BaseModel):
    gold:int = 0

@slow_load_config
class Config(AyakaConfig):
    __config_name__ = box.name
    gold_each_time: int = 1

m10 = on_command("fake_pick", rule=box.rule(states="沙城"))
@m10.handle()
async def get_gold():
    '''捡金子'''
    config = Config()
    cache = box.get_data(Cache2)
    cache.gold += config.gold_each_time
    await m10.send(f"fake +{config.gold_each_time} / {cache.gold}")

# ---------- 8 ----------
from ayaka import Numbers

m11 = on_command("change", rule=box.rule(states="沙城"))
@m11.handle()
async def change_gold_number(nums=Numbers("请输入一个数字")):
    '''修改捡金子配置'''
    config = Config()
    config.gold_each_time = int(nums[0])
    await m11.send(f"修改每次拾取数量为{config.gold_each_time}")
