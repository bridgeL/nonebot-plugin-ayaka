from .onebot import MessageSegment


class TypedMessageSegment(MessageSegment):
    __type__ = ""

    @classmethod
    def check_type(cls, v: MessageSegment):
        return v.type != cls.__type__

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, MessageSegment):
            raise TypeError('MessageSegment required')
        if not cls.check_type(v):
            raise ValueError('invalid MessageSegment format')
        return v

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema["msg_type"] = cls.__type__


class T_Anonymous(TypedMessageSegment):
    __type__ = "anonymous"


class T_At(TypedMessageSegment):
    __type__ = "at"


class T_Contact(TypedMessageSegment):
    __type__ = "contact"


class T_Dice(TypedMessageSegment):
    __type__ = "dice"


class T_Face(TypedMessageSegment):
    __type__ = "face"


class T_Forward(TypedMessageSegment):
    __type__ = "forward"


class T_Image(TypedMessageSegment):
    __type__ = "image"


class T_Json(TypedMessageSegment):
    __type__ = "json"


class T_Location(TypedMessageSegment):
    __type__ = "location"


class T_Music(TypedMessageSegment):
    __type__ = "music"


class T_Node(TypedMessageSegment):
    __type__ = "node"


class T_Poke(TypedMessageSegment):
    __type__ = "poke"


class T_Record(TypedMessageSegment):
    __type__ = "record"


class T_Reply(TypedMessageSegment):
    __type__ = "reply"


class T_Video(TypedMessageSegment):
    __type__ = "video"


class T_Rps(TypedMessageSegment):
    __type__ = "rps"


class T_Shake(TypedMessageSegment):
    __type__ = "shake"


class T_Share(TypedMessageSegment):
    __type__ = "share"


class T_Text(TypedMessageSegment):
    __type__ = "text"


class T_Xml(TypedMessageSegment):
    __type__ = "xml"
