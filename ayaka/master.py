from .box import AyakaBox, get_box, box_list, get_group
from .lazy import on_command, GroupMessageEvent

box = AyakaBox("盒子管理器")
HELP = on_command("盒子帮助", aliases={"box help", "box_help", "box-help"})
STATE = on_command("盒子状态", aliases={"box state", "box_state", "box-state"})


@HELP.handle()
async def show_help():
    if box.arg:
        b = get_box(str(box.arg))
        if b:
            await box.send(b.all_help)
    else:
        infos = [b.all_help for b in box_list]
        await box.send_many(infos)


@STATE.handle()
async def show_state(event: GroupMessageEvent):
    group = get_group(event.group_id)
    if group.current_box_name:
        info = f"正在运行应用[{group.current_box_name}]\n当前状态[{group.state}]"
    else:
        info = "当前没有任何应用在运行"
    await box.send(info)
