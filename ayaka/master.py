from .box import AyakaBox, get_box, box_list, get_group
from .lazy import GroupMessageEvent

box = AyakaBox("盒子管理器")


@box.on_cmd(cmds=["盒子帮助", "box help", "box_help", "box-help", "box帮助"], always=True)
async def show_help():
    '''展示盒子帮助'''
    if box.arg:
        b = get_box(str(box.arg))
        if b:
            await box.send(b.all_help)
    else:
        infos = [b.all_help for b in box_list]
        await box.send_many(infos)


@box.on_cmd(cmds=["盒子状态", "box state", "box_state", "box-state", "box状态"], always=True)
async def show_state(event: GroupMessageEvent):
    group = get_group(event.group_id)
    if group.current_box_name:
        info = f"正在运行应用[{group.current_box_name}]\n当前状态[{group.state}]"
    else:
        info = "当前没有任何应用在运行"
    await box.send(info)
