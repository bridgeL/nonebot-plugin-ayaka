from .box import AyakaBox, get_box, box_list, get_group
from .lazy import GroupMessageEvent

box = AyakaBox("盒子管理器")
'''盒子管理器'''


@box.on_cmd(cmds="盒子帮助", always=True)
async def show_help():
    '''展示盒子帮助'''
    if box.arg:
        name = str(box.arg)
        if name == "全部":
            infos = [b.all_help for b in box_list]
            await box.send_many(infos)
            return

        b = get_box(name)
        if b:
            await box.send(b.all_help)
            return

    if box.group.current_box_name:
        name = box.group.current_box_name
        b = get_box(name)
        if b:
            await box.send(b.all_help)
            return

    infos = [f"[{b.name}]" for b in box_list]
    infos = [
        "已加载的盒子列表",
        " ".join(infos),
        "如果想获得进一步帮助请发送 盒子帮助 <盒子名>，或者发送 盒子帮助 全部"
    ]
    await box.send("\n".join(infos))


@box.on_cmd(cmds="盒子状态", always=True)
async def show_state(event: GroupMessageEvent):
    '''展示盒子状态'''
    group = get_group(event.group_id)
    if group.current_box_name:
        info = f"正在运行应用[{group.current_box_name}]\n当前状态[{group.state}]"
    else:
        info = "当前没有任何应用在运行"
    await box.send(info)
