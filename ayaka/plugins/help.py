from ayaka.lazy import *
from ayaka.model.plugin import prototype_apps as apps


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

    ans = get_help(app_name, app_state, isinstance(
        app.event, GroupMessageEvent))
    await app.send(ans)


def get_help(app_name, app_state, group):
    # 排除隐藏app
    # 排除不符合范围的app
    def check(app: AyakaApp):
        return not app.hide and ((group and app.group) or (not group and app.private))
    _apps = [app for app in apps if check(app)]

    if not app_name:
        names = list(f"[{app.name}]" for app in _apps)
        names.sort()
        return "已安装Ayaka插件\n" + '\n'.join(names)

    help = [app.help for app in _apps if app.name == app_name]
    if not help:
        return "没找到相关帮助"

    help = help[0]

    if not isinstance(help, dict):
        return f"[{app_name}]\n{help}"

    if not app_state or app_state not in help:
        help = "\n\n".join(f"> {k}\n{v}" for k, v in help.items())
        return f"[{app_name}]\n{help}"

    return f"[{app_name} | {app_state}]\n{help[app_state]}"
