from ayaka.lazy import *

app = AyakaApp('帮助', no_storage=True)
app.help = '''
>> 当你在桌面状态下调用 <<
[#help <插件名> <状态>] 查询指定插件在指定状态下的帮助

>> 当你在具体应用中调用 <<
[#help <状态>] 查询该插件在指定状态下的帮助'''


@app.on_command(['help', '帮助'], super=True)
async def help():
    app_name = app.device.running_app_name
    if app_name:
        app_state = app.device.apps[app_name].state
    else:
        app_state = None

    args = app.args

    if app_name:
        if len(args):
            app_state = args[0]

    else:
        if len(args) == 0:
            app_name = ""
            app_state = None
        elif len(args) == 1:
            app_name = args[0]
            app_state = None
        else:
            app_name = args[0]
            app_state = args[1]

    ans = get_help(app_name, app_state, app.event, app.device)
    await app.send(ans)


def get_help(app_name:str, app_state:str, event:MessageEvent, device:AyakaDevice):
    group = isinstance(event, GroupMessageEvent)

    if not app_name:
        # 排除不符合范围的app
        def check(app: AyakaApp):
            return (group and app.group) or (not group and app.private)
        apps = [app for app in device.apps.values() if check(app)]

        # 生成列表
        names = []
        for app in apps:
            s = f"[{app.name}]"
            if not app.valid:
                s += " [已禁用]"
            names.append(s)
        names.sort()
        return "已安装Ayaka插件\n" + '\n'.join(names)

    # 查询
    app = device.get_app(app_name)
    if not app:
        return f"没找到应用[{app_name}]"

    help = app.help
    if not isinstance(help, dict):
        return f"[{app_name}]\n{help}"

    if not app_state or app_state not in help:
        help = "\n\n".join(f"> {k}\n{v}" for k, v in help.items())
        return f"[{app_name}]\n{help}"

    return f"[{app_name} | {app_state}]\n{help[app_state]}"
