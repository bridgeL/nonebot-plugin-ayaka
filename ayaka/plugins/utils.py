import re
import time
from ayaka.lazy import *


def get_time_i():
    '''获得当前时间戳，单位为妙'''
    return int(time.time())


def get_time_s(format: str = '%Y/%m/%d %H:%M:%S'):
    '''获得当前时间字符串，格式由用户自定义'''
    return time.strftime(format, time.localtime())


def time_s2i(time_s: str, format: str = '%Y/%m/%d %H:%M:%S'):
    '''将时间字符串转换为时间戳，需要用户提供其格式'''
    t = time.strptime(time_s, format)
    return int(time.mktime(t))


def time_i2s(time_i: int, format: str = '%Y/%m/%d %H:%M:%S'):
    '''将时间戳转换为时间字符串，格式由用户自定义'''
    t = time.localtime(time_i)
    return time.strftime(format, t)


def time_i_to_date_i(time_i: int):
    '''将时间戳转换为日期编号

    日期编号起点为2000年1月1日'''
    return int((time_i - 1640966400)/86400)


def date_i_to_time_i(date_i: int):
    '''将日期编号转换为时间戳'''
    return date_i*86400 + 1640966400


def time_i_to_local_seconds(time_i: int):
    '''将时间戳转换为从当地0:00:00开始计时的秒数'''
    return (time_i - 57600) % 86400


def get_name(event: GroupMessageEvent):
    return event.sender.card if event.sender.card else event.sender.nickname


async def get_uid_name(bot: Bot, event: GroupMessageEvent, arg: str):
    '''arg: [CQ:at <uid>] | @用户名

    获取该事件所在群聊里，指定用户的uid、名称'''
    uid = 0
    name = ""

    # CQ码
    r = re.search(r"\[CQ:at,qq=(?P<uid>\d+)\]", arg)
    if r:
        uid = int(r.group('uid'))
        data = await bot.get_group_member_info(group_id=event.group_id, user_id=uid)
        name: str = data['card'] if data['card'] else data['nickname']
        return uid, name

    # 文字@，避免小笨蛋复制别人的艾特不生效
    r = re.search(r"@(?P<name>\w+)", arg)
    if r:
        name: str = r.group('name')
        data = await bot.get_group_member_list(group_id=event.group_id)
        for d in data:
            if d['card'] == name or d['nickname'] == name:
                uid: int = d['user_id']
                break

    return uid, name


def force_arg_be_int(args):
    '''读取args的第一个，确保它是int，如果发生错误，返回None'''
    try:
        return int(args[0])
    except:
        return None
