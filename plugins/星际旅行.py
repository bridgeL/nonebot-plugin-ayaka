# # ---------- 1 ----------
# from ayaka import AyakaApp

# app = AyakaApp("星际旅行")
# app.help = "xing ji lv xing"

# # 启动应用
# app.set_start_cmds("星际旅行", "travel")
# # 关闭应用
# app.set_close_cmds("退出", "exit")


# # ---------- 2 ----------
# # 装饰器的顺序没有强制要求
# @app.on_state()
# @app.on_deep_all()
# @app.on_cmd("hi")
# async def say_hi():
#     '''打招呼'''
#     await app.send(f"hi I'm in {app.state}")


# # ---------- 3 ----------
# @app.on_state()
# @app.on_deep_all()
# @app.on_cmd("move")
# async def move():
#     '''移动'''
#     args = [str(a) for a in app.args]
#     await app.set_state(*args)
#     await app.send(f"前往 {app.arg}")


# # ---------- 4 ----------
# # 注册各种行动
# @app.on_state("地球", "月球")
# @app.on_cmd("drink")
# async def drink():
#     '''喝水'''
#     await app.send("喝水")


# @app.on_state("太阳")
# @app.on_deep_all()
# @app.on_cmd("drink")
# async def drink():
#     '''喝太阳风'''
#     await app.send("喝太阳风")


# # ---------- 5 ----------
# @app.on_state("太阳.奶茶店")
# @app.on_cmd("drink")
# async def drink():
#     '''喝奶茶'''
#     await app.send("喝了一口3000度的奶茶")


# # ---------- 6 ----------
# from ayaka import AyakaCache
# class Cache(AyakaCache):
#     ticket: int = 0


# @app.on_state("太阳.售票处")
# @app.on_cmd("buy", "买票")
# async def buy_ticket(cache: Cache):
#     '''买门票'''
#     cache.ticket += 1
#     await app.send("耀斑表演门票+1")


# @app.on_state("太阳")
# @app.on_deep_all()
# @app.on_cmd("watch", "看表演")
# async def watch(cache: Cache):
#     '''看表演'''
#     if cache.ticket <= 0:
#         await app.send("先去售票处买票！")
#     else:
#         cache.ticket -= 1
#         await app.send("10分甚至9分的好看")


# # ---------- 7 ----------
# @app.on_state("太阳.奶茶店")
# @app.on_text()
# async def handle():
#     '''令人震惊的事实'''
#     await app.send("你发现这里只卖热饮")


# # ---------- 8 ----------
# from ayaka import AyakaConfig
# class Config(AyakaConfig):
#     __app_name__ = app.name
#     gold_number: int = 1


# config = Config()


# @app.on_state("太阳.森林公园")
# @app.on_cmd("fake_pick")
# async def get_gold():
#     '''捡金子'''
#     await app.send(f"虚假的喜加一 {config.gold_number}")


# # ---------- 9 ----------
# from pydantic import Field
# from ayaka import AyakaInput
# class UserInput(AyakaInput):
#     number: int = Field(description="一次捡起的金块数量")


# @app.on_state("太阳.森林公园")
# @app.on_cmd("change")
# async def change_gold_number(userinput: UserInput):
#     '''修改捡金子配置'''
#     config.gold_number = userinput.number
#     await app.send("修改成功")


# # ---------- 10 ----------
# @app.on_state("太阳.森林公园")
# @app.on_cmd_regex("一次捡(\d+)块")
# async def change_gold_number():
#     '''修改捡金子配置'''
#     config.gold_number = int(app.cmd_regex.group(1))
#     await app.send("修改成功")
    
    
# # ---------- 11 ----------
# from ayaka import AyakaUserDB
# class Data(AyakaUserDB):
#     __table_name__ = "gold"
#     gold_number: int = 0


# @app.on_state("太阳.森林公园")
# @app.on_cmd("real_pick")
# async def get_gold(data: Data):
#     '''捡金子'''
#     data.gold_number += config.gold_number
#     data.save()
#     await app.send(f"真正的喜加一 {data.gold_number}")

