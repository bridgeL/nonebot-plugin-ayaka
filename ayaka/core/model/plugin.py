import sys
from typing import Callable, List, TYPE_CHECKING, Union
from ...adapter import MessageEvent, Message, MessageSegment, Bot, logger

from .trigger import AyakaTrigger
from .storage import AyakaCache, AyakaStorage


if TYPE_CHECKING:
    from .device import AyakaDevice
    from .bot import AyakaBot

prototype_apps: List["AyakaApp"] = []


class AyakaApp:
    def __init__(self, name, only_group=False, only_private=False, clone=False) -> None:
        '''
        - name 插件名
        - only_group 仅群聊可用 
        - only_private 仅私聊可用 
        '''
        self.module = None
        self.name = name
        self.group = not only_private
        self.private = not only_group
        self._help = "该插件没有提供帮助"
        self.triggers: List[AyakaTrigger] = []

        # 等待具体运行时才会有值
        self.valid = True
        self.state = None
        self.event: MessageEvent = None
        self.message: Message = None
        self.cmd: str = None
        self.args: List[str] = None

        # 等到分配到具体device时才会有值
        self.storage: AyakaStorage = None
        self.cache: AyakaCache = None

        # 循环引用，通过type_checking解决
        self.device: "AyakaDevice" = None
        self.abot: "AyakaBot" = None
        self.bot: Bot = None

        if not clone:
            app_names = [app.name for app in prototype_apps]
            if name in app_names:
                logger.warning(f"应用[<y>{name}</y>]重名！可能会导致device无法查找到app！")
            prototype_apps.append(self)


    def clone(self, device: "AyakaDevice", abot: "AyakaBot"):
        app = AyakaApp(self.name, clone=True)
        app.module = self.module
        app.name = self.name
        app.group = self.group
        app.private = self.private
        app.help = self.help
        app.triggers = self.triggers

        # 修改trigger里的app
        for t in app.triggers:
            t.app = app

        # 生成 storage
        app.storage = AyakaStorage(
            "data", "storage", abot.bot.self_id,
            device.device_id, f"{app.name}.json",
            default="{}"
        )
        
        # 是否 启用/禁用
        app.valid = app.storage.accessor("_permit").get(True)

        # 生成
        app.cache = AyakaCache()
        app.device = device
        app.abot = abot
        app.bot = abot.bot
        return app

    @property
    def help(self):
        return self._help

    @help.setter
    def help(self, help):
        self._help = help

    def on(self, cmds, states, super):
        cmds = ensure_list(cmds)
        states = ensure_list(states)

        def decorator(func: Callable[[], None]):
            # 注 册 出 生 地
            if not self.module:
                self.module = sys.modules[func.__module__]

            # 注册处理回调
            for state in states:
                for cmd in cmds:
                    t = AyakaTrigger(
                        self, cmd, state, super, self.group, self.private, func
                    )
                    self.triggers.append(t)
            return func

        return decorator

    def on_command(self, cmds, states=None, super=False):
        return self.on(cmds=cmds, states=states, super=super)

    def on_text(self, states=None, super=False):
        return self.on(cmds=None, states=states, super=super)

    def start(self, state: str):
        return self.device.start_app(self, state)

    def close(self):
        return self.device.close_app()

    async def send(self, msg: Union[str, Message, MessageSegment]):
        await self.bot.send(self.event, msg)

    def is_running(self):
        return self.device.running_app == self

    def switch(self):
        for k, v in self.module.__dict__.items():
            if isinstance(v, AyakaApp):
                self.module.__dict__[k] = self


def ensure_list(data):
    if type(data) is str:
        return [data]

    try:
        return list(data)
    except:
        return [data]
