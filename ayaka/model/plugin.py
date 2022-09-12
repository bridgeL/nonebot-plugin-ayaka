import importlib
from pathlib import Path
from typing import Callable, List, TYPE_CHECKING, Union


from .trigger import Trigger
from .storage import Cache, Storage

# 此处本应有依赖倒置，但是懒了
from nonebot.adapters.onebot.v11 import MessageEvent, Message, MessageSegment

if TYPE_CHECKING:
    from .device import AyakaDevice
    from .bot import AyakaBot, Bot

prototype_apps: List["AyakaApp"] = []
workspace_path = Path(".").resolve()


class AyakaApp:
    def __init__(self, name, only_group=False, only_private=False, no_storage=False, clone=False) -> None:
        '''
        - name 插件名
        - only_group 仅群聊可用 
        - only_private 仅私聊可用 
        - no_storage 不使用默认的storage
        '''
        self.module = None

        if not clone:
            prototype_apps.append(self)

        self.name = name
        self.group = not only_private
        self.private = not only_group
        self.no_storage = no_storage
        self._help = "该插件没有提供帮助"
        self.super_triggers: List[Trigger] = []
        self.state_triggers: List[Trigger] = []
        self.desktop_triggers: List[Trigger] = []

        # 等待具体运行时才会有值
        self.valid = True
        self.state = None
        self.event: MessageEvent = None
        self.message: Message = None
        self.cmd: str = None
        self.args: List[str] = None

        # 等到分配到具体device时才会有值
        self.storage: Storage = None
        self.cache: Cache = None

        # 循环引用，通过type_checking解决
        self.device: "AyakaDevice" = None
        self.abot: "AyakaBot" = None
        self.bot: "Bot" = None

    def clone(self, device: "AyakaDevice", abot: "AyakaBot"):
        app = AyakaApp(self.name, clone=True)
        app.module = self.module
        app.name = self.name
        app.valid = self.valid
        app.group = self.group
        app.private = self.private
        app.no_storage = self.no_storage
        app.help = self.help
        app.super_triggers = self.super_triggers
        app.state_triggers = self.state_triggers
        app.desktop_triggers = self.desktop_triggers

        # 生成
        if not self.no_storage:
            app.storage = Storage(
                "data", "storage", abot.bot.self_id,
                device.device_id, f"{app.name}.json", 
                default="{}"
            )
        app.cache = Cache()
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
                self.module = importlib.import_module(func.__module__)

            # 注册处理回调
            for state in states:
                for cmd in cmds:
                    t = Trigger(
                        self.name, cmd, state, super, self.group, self.private, func
                    )
                    if super:
                        self.super_triggers.append(t)
                    elif not state:
                        self.desktop_triggers.append(t)
                    else:
                        self.state_triggers.append(t)
            return func

        return decorator

    def on_command(self, cmds, states=None, super=False):
        return self.on(cmds=cmds, states=states, super=super)

    def on_text(self, states=None, super=False):
        return self.on(cmds=None, states=states, super=super)

    def start(self, state: str):
        return self.device.start_app(self.name, state)

    def close(self):
        return self.device.close_app()

    async def send(self, msg: Union[str, Message, MessageSegment]):
        await self.bot.send(self.event, msg)

    def is_running(self):
        return self.device.running_app_name == self.name


def ensure_list(data):
    if type(data) is str:
        return [data]

    try:
        return list(data)
    except:
        return [data]
