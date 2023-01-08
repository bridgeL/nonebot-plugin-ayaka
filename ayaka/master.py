'''盒子管理器'''
from .box import AyakaBox, get_box, box_list
from .helpers import run_in_startup


@run_in_startup
async def startup():
    '''延迟加载'''
    box = AyakaBox("盒子管理器")
    '''盒子管理器'''

    @box.on_cmd(cmds="盒子列表", always=True)
    async def list_box():
        '''展示所有盒子'''
        infos = ["已加载的盒子列表"]
        for b in box_list:
            info = f"- [{b.name}]"
            if not b.valid:
                info += " [已被屏蔽]"
            infos.append(info)
        await box.send("\n".join(infos))

    @box.on_cmd(cmds="盒子帮助", always=True)
    async def show_help():
        '''展示盒子帮助'''
        if box.arg:
            name = str(box.arg)
            b = get_box(name)
            if b:
                await box.send(b.help)
                return
            else:
                await box.send("没有找到对应盒子")

        b = box.group.current_box
        if b:
            await box.send(b.help)
            return

        await list_box()
        infos = [
            "如果想获得进一步帮助请使用命令",
            "- 盒子帮助 <盒子名>",
            "- 全部盒子帮助"
        ]
        await box.send("\n".join(infos))

    @box.on_cmd(cmds="全部盒子帮助", always=True)
    async def show_help():
        '''展示展示所有盒子的帮助'''
        infos = [b.help for b in box_list]
        await box.send_many(infos)

    @box.on_cmd(cmds="盒子状态", always=True)
    async def show_state():
        '''展示盒子状态'''
        b = box.group.current_box
        if b:
            info = f"正在运行盒子[{b.name}]\n当前状态[{b.state}]"
        else:
            info = "当前没有任何盒子在运行"
        await box.send(info)

    @box.on_cmd(cmds="强制退出", always=True)
    async def force_exit():
        '''强制关闭当前盒子'''
        b = box.group.current_box
        if b:
            await b.close()

    @box.on_cmd(cmds="屏蔽盒子", always=True)
    async def block_box():
        '''<盒子名> 屏蔽盒子'''
        if not box.arg:
            await box.send("请使用 屏蔽盒子 <盒子名>")
            return

        name = str(box.arg)
        b = get_box(name)
        if not b:
            await box.send("没有找到对应盒子")
            return

        await b.close()
        b.valid = False
        await box.send(f"已屏蔽盒子 {name}")

    @box.on_cmd(cmds="取消屏蔽盒子", always=True)
    async def block_box():
        '''<盒子名> 取消屏蔽盒子'''
        if not box.arg:
            await box.send("请使用 取消屏蔽盒子 <盒子名>")
            return

        name = str(box.arg)
        if name == box.name:
            await box.send("不可屏蔽盒子管理器")
            return

        b = get_box(name)
        if not b:
            await box.send("没有找到对应盒子")
            return

        b.valid = True
        await box.send(f"已取消屏蔽盒子 {name}")
