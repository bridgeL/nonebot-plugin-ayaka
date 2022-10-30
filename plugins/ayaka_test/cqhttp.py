'''简单模拟cqhttp'''
from .core import fake_qq, bot_id


# message 可能是cqhttp格式的node数组
def handle_message(message):
    if isinstance(message, list):
        def handle(node: dict):
            if node["type"] == "text":
                return node["data"]["text"]
            return str(node)
        return "".join(handle(m) for m in message)
    return str(message)


@fake_qq.on_cqhttp("send_group_msg")
async def group_msg(echo: int, params: dict):
    gid = params["group_id"]
    text = handle_message(params["message"])
    fake_qq.print(f"群聊({gid}) <r>bot</r>({bot_id}) 说：\n{text}")
    await fake_qq.send_echo(echo, None)


@fake_qq.on_cqhttp("send_group_forward_msg")
async def _(echo: int, params: dict):
    gid = params["group_id"]
    messages = params["messages"]
    for m in messages:
        uid = m["data"]["user_id"]
        name = m["data"]["nickname"]
        text = m["data"]["content"]
        fake_qq.print(f"群聊({gid}) <y>{name}</y>({uid}) 说：\n{text}")
    await fake_qq.send_echo(echo, None)


@fake_qq.on_cqhttp("send_private_msg")
async def private_msg(echo: int, params: dict):
    uid = params["user_id"]
    text = handle_message(params["message"])
    fake_qq.print(f"<r>bot</r>({bot_id}) 对私聊({uid}) 说：\n{text}")
    await fake_qq.send_echo(echo, None)


# 公用一个，挤挤吧
@fake_qq.on_cqhttp("get_group_member_list", "get_friend_list")
async def _(echo: int, params: dict):
    # 假装这个群有10个人，分别叫测试1-10号
    await fake_qq.send_echo(echo, [
        {
            "user_id": i,
            "card": f"测试{i}号",
            "nickname": f"测试{i}号"
        } for i in range(10)
    ])


@fake_qq.on_cqhttp("send_msg")
async def _(echo: int, params: dict):
    message_type = params["message_type"]
    if message_type == "group":
        await group_msg(echo, params)
    else:
        await private_msg(echo, params)
