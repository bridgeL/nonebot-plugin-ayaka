from typing import Optional
from loguru import logger


def bool_to_str(b: Optional[bool]) -> Optional[str]:
    """转换布尔值为字符串。"""
    return b if b is None else str(b).lower()


def escape(s: str, *, escape_comma: bool = True) -> str:
    """
    :说明:

      对字符串进行 CQ 码转义。

    :参数:

      * ``s: str``: 需要转义的字符串
      * ``escape_comma: bool``: 是否转义逗号（``,``）。
    """
    s = s.replace("&", "&amp;").replace("[", "&#91;").replace("]", "&#93;")
    if escape_comma:
        s = s.replace(",", "&#44;")
    return s


def unescape(s: str) -> str:
    """
    :说明:

      对字符串进行 CQ 码去转义。

    :参数:

      * ``s: str``: 需要转义的字符串
    """
    return s.replace("&#44;", ",").replace("&#91;", "[").replace("&#93;", "]").replace("&amp;", "&")
    


# def safe_cqhttp_utf8(api, data):
#     if api in ["send_msg", "send_group_msg", "send_private_msg"]:
#         data["message"] = cqhttp_fuck(
#             data["message"], [119, 121, 123, 125])

#     if api == "send_group_forward_msg":
#         # 对每个node都要fuck一遍
#         nodes = data['messages']
#         for node in nodes:
#             node['data']['content'] = cqhttp_fuck(
#                 node['data']['content'], [58, 60])
#         data['messages'] = nodes

#     return data


# def cqhttp_fuck(msg, ban_range: list):
#     """ 傻逼风控
#         该长度其实也不单是根据encode utf8长度来判断，还要根据html转义前的utf8长度判断。。傻逼
#         比如&#91;占5个长度，其实相当于1个长度
#     """
#     # 获取utf8长度
#     s = str(msg)
#     s = unescape(s)
#     s = s.encode('utf8')
#     length = len(s)

#     logger.opt(colors=True).debug(f"转义前utf8字符长度 <y>{length}</y>")

#     if length in ban_range:
#         return str(msg) + " "
#     return msg
