from .ayaka import app_list, AyakaApp

app = AyakaApp("ayaka_master")
app.help = '''ayaka综合管理模块'''


@app.on.idle(super=True)
@app.on.command("启用", "permit")
async def permit():
    ''' '''
    if not app.args:
        await app.send("参数缺失")
        return

    name = str(app.args[0])
    f = app.group.permit_app(name)
    if f:
        await app.send(f"已启用应用 [{name}]")
    else:
        await app.send(f"应用不存在 [{name}]")


@app.on.idle(super=True)
@app.on.command("禁用", "forbid")
async def forbid():
    ''' '''
    if not app.args:
        await app.send("参数缺失")
        return

    name = str(app.args[0])
    f = app.group.forbid_app(name)
    if f:
        await app.send(f"已禁用应用 [{name}]")
    else:
        await app.send(f"应用不存在 [{name}]")


@app.on.idle(super=True)
@app.on.command("插件", "plugin", "plugins")
async def show_plugins():
    ''' '''
    items = []
    for _app in app_list:
        s = ""
        if not _app.valid:
            s = "[已禁用] "
        info = f"[{_app.name}] {s}"
        items.append(info)
    await app.send("\n".join(items))


@app.on.idle(super=True)
@app.on.command("状态", "state")
async def show_state():
    ''' '''
    name = app.group.running_app_name
    if not name:
        await app.send("当前设备处于闲置状态")
        return
    info = f"正在运行应用 [{name}|{app.group.running_app.state}]"
    await app.send(info)


@app.on.idle(super=True)
@app.on.command("帮助", "help")
async def show_help():
    ''' '''
    _app = app.group.running_app
    # 没有应用正在运行
    if not _app:
        # 查询指定应用的详细帮助
        if app.args:
            name = str(app.args[0])
            _app = app.group.get_app(name)
            if not _app:
                await app.send(f"应用不存在 [{name}]")
                return
            # 详细帮助
            await app.send(_app.all_help)
            return

        # 展示所有应用
        items = []
        for _app in app_list:
            info = f"[{_app.name}]\n{_app.intro}"
            items.append(info)
        await app.send_many(items)

        await app.send("使用 帮助 <插件名> 可以展示该插件的详细帮助信息")
        return

    # 展示当前应用当前状态的帮助
    await app.send(_app.help)


@app.on.idle(super=True)
@app.on.command("强制退出", "force_exit")
async def force_exit():
    ''' '''
    _app = app.group.running_app
    if _app:
        await _app.close()
