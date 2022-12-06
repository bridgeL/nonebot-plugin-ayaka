# 这是个糟糕的功能，应该把他包装到更有意义的使用场景中


# '''序列化'''
# import json
# from .driver import Message, MessageSegment, DataclassEncoder


# class AyakaParser:
#     def encode_message(self, data):
#         if not isinstance(data, Message):
#             data = Message(data)
#         return json.dumps(data, ensure_ascii=False, cls=DataclassEncoder)

#     def decode_message(self, text: str):
#         data = json.loads(text)

#         def func(d: dict):
#             type = d["type"]
#             data = d["data"]
#             return getattr(MessageSegment, type)(**data)

#         return Message(func(d) for d in data)


# parser = AyakaParser()
