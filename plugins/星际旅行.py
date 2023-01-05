# ---------- 1 ----------
from ayaka import AyakaBox

box = AyakaBox("星际旅行")
box.help = "xing ji lv xing"

# 启动应用
box.set_start_cmds(cmds=["星际旅行", "travel"])
# 关闭应用
box.set_close_cmds(cmds=["退出", "exit"])

# ---------- 2 ----------
@box.on_cmd(cmds="move", states="*")
async def move():
    '''移动'''
    arg = str(box.arg)
    await box.set_state(arg)
    await box.send(f"前往 {arg}")
    
# ---------- 3 ----------
@box.on_cmd(cmds="hi", states=["地球", "月球", "太阳"])
async def say_hi():
    '''打招呼'''
    await box.send(f"你好，{box.state}！")

# ---------- 4 ----------
# 相同命令，不同行为
@box.on_cmd(cmds="drink", states=["地球", "月球"])
async def drink():
    '''喝水'''
    await box.send("喝水")

@box.on_cmd(cmds="drink", states="太阳")
async def drink():
    '''喝太阳风'''
    await box.send("喝太阳风")

# ---------- 5 ----------
from ayaka import BaseModel

class Cache(BaseModel):
    ticket:int = 0

@box.on_cmd(cmds=["buy", "买票"], states="售票处")
async def buy_ticket():
    '''买门票'''
    cache = box.get_data(Cache)
    cache.ticket += 1
    await box.send("耀斑表演门票+1")

@box.on_cmd(cmds=["watch", "看表演"], states="*")
async def watch():
    '''看表演'''
    cache = box.get_data(Cache)
    if cache.ticket <= 0:
        await box.send("先去售票处买票！")
    else:
        cache.ticket -= 1
        await box.send("门票-1")
        await box.send("10分甚至9分的好看")

# ---------- 6 ----------
@box.on_text(states="火星")
async def handle():
    '''令人震惊的事实'''
    await box.send("你火星了")

# ---------- 7 ----------
from ayaka import AyakaConfig, slow_load_config

class Cache2(BaseModel):
    gold:int = 0

@slow_load_config
class Config(AyakaConfig):
    __config_name__ = box.name
    gold_each_time: int = 1

@box.on_cmd(cmds="fake_pick", states="沙城")
async def get_gold():
    '''捡金子'''
    config = Config()
    cache = box.get_data(Cache2)
    cache.gold += config.gold_each_time
    await box.send(f"fake +{config.gold_each_time} / {cache.gold}")

# ---------- 8 ----------
from ayaka import Numbers

@box.on_cmd(cmds="change", states="沙城")
async def change_gold_number(nums=Numbers("请输入一个数字")):
    '''修改捡金子配置'''
    config = Config()
    config.gold_each_time = int(nums[0])
    await box.send(f"修改每次拾取数量为{config.gold_each_time}")

# ---------- 9 ----------
from ayaka import AyakaBox, AyakaUserDB

class UserGold(AyakaUserDB):
    __table_name__ = "user_gold"
    value:int = 0

@box.on_cmd(cmds="real_pick", states="沙城")
async def get_gold():
    '''捡金子'''
    config = Config()
    gold = UserGold.select_one(
        group_id = box.group_id,
        user_id = box.user_id
    )
    gold.value += config.gold_each_time
    gold.save()
    await box.send(f"real +{config.gold_each_time} / {gold.value}")
