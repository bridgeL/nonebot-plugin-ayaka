from asyncio import sleep
from random import randint
from typing import List
from ayaka.lazy import *
from ayaka.plugins.bag import add_money
from ayaka.plugins.utils import get_name, force_arg_be_int, get_time_s
logger.success(f"Succeeded to import \"<y>{__name__}</y>\"")

class BetUser:
    '''一个简单的封装'''

    def __init__(self, name: str, uid: int) -> None:
        self.name = name
        self.uid = uid
        self.chip = 10
        self.num = randint(0, 100)
        self.win = 0

    @property
    def data(self):
        return self.chip + self.num

    @property
    def profit(self):
        return self.win - self.chip


app = AyakaApp("赌大小", only_group=True)
app.help = '''赌大小
[#bet/赌大小] 发起房间
[#statistic/统计] 展示个人统计数据
[#clear/清除统计] 清除个人统计数据
[#join/加入] 加入房间
[#start/开始] 开始游戏
[#break/打断] 掀桌子~
[<数字>] 设置筹码，不设置则默认为10
规则：每人会收到0-100间的一个数字，之后每人给出一份筹码（10-100），最后，筹码+点数最大的人获得全场的筹码
'''


@app.on_command(["赌大小", "bet"])
async def start():
    # 加入游戏前必须是bot好友
    if not await app.abot.is_friend(app.event.user_id):
        await app.send(f"[{get_name(app.event)}] 还不是bot的好友，没法发起游戏")
        return

    f, info = app.start("room")
    await app.send(info)

    # 开启app出错
    if not f:
        return

    name = get_name(app.event)
    app.cache.users = [BetUser(name, app.event.user_id)]
    await app.send("房间已创建")
    await app.send(f"[{name}]加入房间成功")


@app.on_command(["退出", "exit"], "room")
async def close_room():
    uid = app.event.user_id
    users: List[BetUser] = app.cache.users

    # 排除外人搅局
    if not get_user(users, uid):
        name = get_name(app.event)
        await app.send(f"[{name}] 没有参与游戏")
        return

    f, info = app.close()
    await app.send(info)


@app.on_command(["加入", "join"], "room")
async def join_room():
    uid = app.event.user_id
    name = get_name(app.event)
    users: List[BetUser] = app.cache.users

    # 确认好友
    if not await app.abot.is_friend(uid):
        await app.send(f"[{name}] 还不是bot的好友，没法加入游戏")
        return

    # 重复加入
    u = get_user(users, uid)
    if u:
        await app.send(f"[{u.name}]已加入房间了")
        return

    users.append(BetUser(name, uid))
    await app.send(f"[{name}]加入房间成功")


@app.on_command(["开始", "start"], "room")
async def start_game():
    uid = app.event.user_id
    users: List[BetUser] = app.cache.users

    # 排除外人搅局
    if not get_user(users, uid):
        name = get_name(app.event)
        await app.send(f"[{name}] 没有参与游戏")
        return

    # 人数不足
    if len(users) < 2:
        await app.send("人数不足两人，请邀请更多人加入")
        return

    await app.send("游戏开始，请参与者给出筹码，默认10")

    # 私聊点数
    for u in users:
        word = f"[{u.name}] 的点数为 {u.num}"
        await app.bot.send_private_msg(user_id=u.uid, message=word)
        app.storage.accessor(u.uid, "cnt").inc()

    # 进入下一状态
    app.state = "bet"

    # 等待一段时间后开始
    await sleep(10)
    if not app.is_running():
        return

    await app.send("游戏将在10s后自动开奖")
    for i in range(10):
        await app.send(str(10-i))
        await sleep(1)
        if not app.is_running():
            return

    # 计算奖金
    prize = sum(u.chip for u in users)

    # 查找赢家，生成公示结果
    words = ""

    max_users = []
    max_data = 0
    for u in users:
        data = u.data
        word = f"[{u.name}] 的点数为 {u.num}，筹码为{u.chip}，合计{data}"
        words += word + "\n"

        if data > max_data:
            max_users = [u]
            max_data = data
        elif data == max_data:
            max_users.append(u)

    # 计算奖励
    diff = prize // len(max_users)

    # 公布结果
    await app.send(words.strip("\n"))

    for u in max_users:
        u.win = diff
        app.storage.accessor(u.uid, "win").inc()
        await app.send(f"[{u.name}] 赢了，扣除筹码后，获得 {u.profit}金")

    # 结算奖励
    for u in users:
        add_money(u.profit, app.device, u.uid)
        sa = app.storage.accessor(u.uid, "money")
        sa.set(sa.get(0) + u.profit)

    # 关闭应用
    f, info = app.close()
    await app.send(info)


@app.on_text("bet")
async def set_chip():
    uid = app.event.user_id
    name = get_name(app.event)
    users: List[BetUser] = app.cache.users

    # 排除外人搅局
    if not get_user(users, uid):
        await app.send(f"[{name}] 没有参与游戏")
        return

    # 强制转换
    chip = force_arg_be_int(app.args)
    if chip is None:
        return

    # 范围控制
    chip = min(100, max(10, chip))

    u = get_user(users, uid)
    u.chip = chip
    await app.send(f"[{name}] 设置筹码为 {chip}")


@app.on_command(["打断", "break"], "bet")
async def set_chip():
    uid = app.event.user_id
    name = get_name(app.event)
    users: List[BetUser] = app.cache.users

    # 排除外人搅局
    if not get_user(users, uid):
        await app.send(f"[{name}] 没有参与游戏")
        return

    # 计算奖金
    prize = sum(u.chip for u in users)

    # 扣除2倍
    add_money(-2*prize, app.device, uid)
    await app.send(f"[{name}] 见势不妙掀翻了桌子，归还除他外的所有人的筹码，[{name}]被扣除总池筹码的2倍，失去 {2*prize}金")

    app.storage.accessor(uid, "break").inc()
    sa = app.storage.accessor(uid, "money")
    sa.set(sa.get(0) - 2*prize)

    # 房间关闭
    f, info = app.close()
    await app.send(info)


@app.on_command(["统计", "statistic"], "room")
async def handle():
    uid = app.event.user_id
    name = get_name(app.event)
    cnt = app.storage.accessor(uid, "cnt").get(0)
    win = app.storage.accessor(uid, "win").get(0)
    _break = app.storage.accessor(uid, "break").get(0)
    money = app.storage.accessor(uid, "money").get(0)
    date = app.storage.accessor(uid, "date").get("第一次参与")
    word = f"[{name}] 自{date}以来\n总计参加了{cnt}次\n赢得了{win}次\n掀桌了{_break}次\n总计赢得了 {money}金"
    await app.send(word)


@app.on_command(["清除统计", "clear"], "room")
async def handle():
    uid = app.event.user_id
    name = get_name(app.event)
    app.storage.accessor(uid, "cnt").set(0)
    app.storage.accessor(uid, "win").set(0)
    app.storage.accessor(uid, "break").set(0)
    app.storage.accessor(uid, "money").set(0)
    app.storage.accessor(uid, "date").set(get_time_s("%Y/%m/%d"))
    await app.send(f"[{name}] 已成功清除统计记录")


def get_user(users: List[BetUser], uid):
    '''检查该用户是否在游戏内，返回该用户'''
    for u in users:
        if u.uid == uid:
            return u
