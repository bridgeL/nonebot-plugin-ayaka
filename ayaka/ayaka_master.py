'''ayaka综合管理模块'''
from pydantic import Field
from .ayaka_input import AyakaInputModel
from .ayaka import app_list, AyakaApp
from .constant import get_app
from .config import ayaka_root_config
from .state import root_state

app = AyakaApp("ayaka_master")
app.help = '''ayaka综合管理模块'''


class UidInput(AyakaInputModel):
    uid: int = Field(description="QQ号")

# @app.on.idle(super=True)
# @app.on.command("启用", "permit")
# async def permit():
#     
#     if not app.args:
#         await app.send("参数缺失")
#         return

#     name = str(app.args[0])
#     f = app.group.permit_app(name)
#     if f:
#         await app.send(f"已启用应用 [{name}]")
#     else:
#         await app.send(f"应用不存在 [{name}]")


# @app.on.idle(super=True)
# @app.on.command("禁用", "forbid")
# async def forbid():
#     
#     if not app.args:
#         await app.send("参数缺失")
#         return

#     name = str(app.args[0])
#     f = app.group.forbid_app(name)
#     if f:
#         await app.send(f"已禁用应用 [{name}]")
#     else:
#         await app.send(f"应用不存在 [{name}]")


@app.on.idle(super=True)
@app.on.command("插件", "plugin", "plugins")
async def show_plugins():
    # 展示所有应用
    items = []
    for _app in app_list:
        s = "[已禁用] " if not _app.valid else ""
        info = f"[{_app.name}] {s}"
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
async def show_help():
    # 展示当前应用当前状态的帮助
    if app.state > root_state:
        _app = get_app(app.state.keys[1])
        await app.send(_app.help)
        return

    # 没有应用正在运行
    # 查询指定应用的详细帮助
    if app.args:
        name = str(app.args[0])
        _app = get_app(name)
        if not _app:
            await app.send(f"应用不存在 [{name}]")
            return

        # 详细帮助
        s = "[已禁用] " if not _app.valid else ""
        info = f"[{_app.name}] {s}\n{_app.all_help}"
        await app.send(info)
        return

    # 展示所有应用介绍
    items = ["所有应用介绍一览"]
    for _app in app_list:
        s = "[已禁用] " if not _app.valid else ""
        info = f"[{_app.name}] {s}\n{_app.intro}"
        items.append(info)

    await app.send_many(items)
    await app.send("使用 帮助 <插件名> 可以进一步展示指定插件的详细帮助信息")


@app.on.idle(super=True)
@app.on.command("强制退出", "force_exit")
async def force_exit():
    await app.group.goto(root_state)
    await app.send("已强制退出应用")


@app.on.idle(super=True)
@app.on.command("add_admin")
@app.on_model(UidInput)
async def add_admin():
    '''增加ayaka管理者'''
    if app.user_id not in ayaka_root_config.owners:
        await app.send("仅有ayaka所有者有权执行此命令")
        return

    try:
        uid = int(str(app.args[0]))
    except:
        await app.send("设置失败")
        return

    if uid not in ayaka_root_config.admins:
        ayaka_root_config.admins.append(uid)
        ayaka_root_config.force_update()

    await app.send("设置成功")


@app.on.idle(super=True)
@app.on.command("remove_admin")
@app.on_model(UidInput)
async def remove_admin():
    '''移除ayaka管理者'''
    if app.user_id not in ayaka_root_config.owners:
        await app.send("仅有ayaka所有者有权执行此命令")
        return

    try:
        uid = int(str(app.args[0]))
    except:
        await app.send("设置失败")
        return

    if uid in ayaka_root_config.admins:
        ayaka_root_config.admins.remove(uid)
        ayaka_root_config.force_update()

    await app.send("设置成功")
