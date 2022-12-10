'''ayaka综合管理模块'''
from pydantic import Field
from .ayaka import app_list, AyakaApp, get_app
from .config import ayaka_root_config, save
from .state import root_state
from .driver import get_driver
from .depend import commit, AyakaInput

driver = get_driver()

app = AyakaApp("ayaka_master")
app.help = '''ayaka综合管理模块'''


class UidInput(AyakaInput):
    uid: int = Field(description="QQ号", gt=0)


class AppnameInput(AyakaInput):
    name: str = Field("", description="应用名")


@app.on.idle(super=True)
@app.on.command("插件", "plugin", "plugins")
async def show_plugins():
    '''展示所有应用'''
    items = []
    for _app in app_list:
        info = f"[{_app.name}]"
        items.append(info)
    await app.send("\n".join(items))


@app.on.idle(super=True)
@app.on.command("状态", "state")
async def show_state():
    state = app.group.state
    if state <= root_state:
        await app.send("当前设备处于闲置状态")
        return
    await app.send(f"当前状态：{state}")


@app.on.idle(super=True)
@app.on.command("帮助", "help")
async def show_help(data: AppnameInput):
    # 展示当前应用当前状态的帮助
    if app.state > root_state:
        app_name = app.state.keys[1]
        _app = get_app(app_name)
        await app.send(_app.help)
        return

    # 没有应用正在运行
    # 查询指定应用的详细帮助
    name = data.name
    if name:
        _app = get_app(name)
        if not _app:
            await app.send(f"应用不存在 [{name}]")
            return

        # 详细帮助
        info = f"[{_app.name}]\n{_app.all_help}"
        await app.send(info)
        return

    # 展示所有应用介绍
    items = ["所有应用介绍一览"]
    for _app in app_list:
        info = f"[{_app.name}]\n{_app.intro}"
        items.append(info)

    await app.send_many(items)
    await app.send("使用 帮助 <插件名> 可以进一步展示指定插件的详细帮助信息")


@app.on.idle(super=True)
@app.on.command("强制退出", "force_exit")
async def force_exit():
    await app.group.goto(root_state)
    await app.send("已强制退出应用")


@app.on.idle(super=True)
@app.on.command("查看缓存")
async def show_cache():
    '''查看当前群组的所有缓存'''
    print(app.group.cache_dict)


@app.on.idle(super=True)
@app.on.command("add_admin")
async def add_admin(data: UidInput):
    '''增加ayaka管理者'''
    if app.user_id not in ayaka_root_config.owners:
        await app.send("仅有ayaka所有者有权执行此命令")
        return

    uid = data.uid

    if uid not in ayaka_root_config.admins:
        ayaka_root_config.admins.append(uid)
        ayaka_root_config.force_update()

    await app.send("设置成功")


@app.on.idle(super=True)
@app.on.command("remove_admin")
async def remove_admin(data: UidInput):
    '''移除ayaka管理者'''
    if app.user_id not in ayaka_root_config.owners:
        await app.send("仅有ayaka所有者有权执行此命令")
        return

    uid = data.uid

    if uid in ayaka_root_config.admins:
        ayaka_root_config.admins.remove(uid)
        ayaka_root_config.force_update()

    await app.send("设置成功")


# 定时提交db、保存setting
@app.on.interval(60, show=False)
async def update_data():
    commit()
    save()


# 退出提交
@driver.on_shutdown
async def update_data():
    commit()
    save()
