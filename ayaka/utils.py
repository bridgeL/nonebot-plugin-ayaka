# def singleton(cls):
#     '''单例模式的装饰器'''
#     instance = None

#     def getinstance(*args, **kwargs):
#         nonlocal instance
#         if instance is None:
#             instance = cls(*args, **kwargs)
#         return instance

#     return getinstance

# class UserInput(AyakaInput):
#     '''将用户输入的第一个参数（QQ号/群名片/@xxx）自动转换为User对象'''
#     user: Optional[User] = Field(description="查询目标的QQ号/名称/@xx")

#     @classmethod
#     async def create_by_app_get_params(cls, app: AyakaApp):
#         args = app.args
#         props = cls.props()
#         params = {k: v for k, v in zip(props, args)}
#         if args:
#             params["user"] = await get_user(app, args[0])
#         return params
