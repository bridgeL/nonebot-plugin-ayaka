from collections import defaultdict
from typing import List, Type, TypeVar, Union
from pydantic import BaseModel

from nonebot import on_command, on_message
from nonebot.internal.matcher import current_event
from nonebot.internal.rule import Rule
from nonebot.adapters.onebot.v11 import GroupMessageEvent


T_BaseModel = TypeVar("T_BaseModel", bound=BaseModel)


class AyakaState:
    '''群组状态

    属性:
        state: 群组状态全称
        parts: 群组状态的各级名称
    '''

    def __str__(self) -> str:
        return self.state

    def __repr__(self) -> str:
        return str(self)

    def __init__(self, state: str) -> None:
        '''创建state对象

        参数:
            state: 字符串，通过"."分割为多级
        '''
        if not state:
            raise Exception("state不可为空字符串")
        self.state = state
        self.parts = state.split(".")

    def belong(self, parent: "AyakaState"):
        '''判断 自身 是否是 parent 的子状态

        参数:
            parent: 疑似的父状态

        返回:
            deep: 子状态位于父状态的第几层

                0: "子状态"与"父状态"完全相同

                1: 子状态是父状态的第一代孩子，例如：

                    child = AyakaState("root.test")
                    parent = AyakaState("root")
                    child.belong(parent) == 1

                -1: "子状态"不是"父状态"的孩子：

                    child = AyakaState("root")
                    parent = AyakaState("test")
                    child.belong(parent) == -1
        '''
        child_len = len(self.parts)
        parent_len = len(parent.parts)
        n = min(child_len, parent_len)

        for i in range(n):
            if self.parts[i] != parent.parts[i]:
                return -1

        deep = child_len - parent_len
        if deep < 0:
            return -1

        return deep

    def __getattr__(self, key: str):
        return self.join(key)

    def join(self, key: str):
        return AyakaState(f"{self.state}.{key}")


root_state = AyakaState("root")
'''根状态，群组状态的初始值，同时也是所有状态的第一级'''


class AyakaGroup:
    '''群组

    属性:
        state: group当前所处状态，初始值为根状态
        cache: group当前缓存的数据，不会随事件结束而清除
        group_id: 群组qq号
    '''

    def __init__(self, group_id: int) -> None:
        self.state = root_state
        self.cache = defaultdict(dict)
        self.group_id = group_id


group_list: List[AyakaGroup] = []
'''群组列表'''


def get_group(group_id: int):
    '''获得群组对象，若不存在则自动新增'''
    for group in group_list:
        if group.group_id == group_id:
            return group
    group = AyakaGroup(group_id)
    group_list.append(group)
    return group


class AyakaBox:
    '''盒子，通过盒子使用ayaka的大部分特性

    属性:
        name: box的名字，应与插件名字一致
        group: box当前正在处理的群组
        state: box当前正在处理的群组的状态
        cache: box当前正在处理的群组的缓存数据空间中，分配给该box的独立字典

    示例代码1:
    ```
        from ayaka.box import AyakaBox
        from nonebot import on_message

        box = AyakaBox("测试")
        matcher = on_message(rule=box.create_state_checker())

        @matcher.handle()
        async def matcher_handle():
            print(box.group, box.group.group_id)
    ```
    示例代码2:
    ```
        from ayaka.box import AyakaBox

        box = AyakaBox("测试")
        matcher = box.create_text_matcher()

        @matcher.handle()
        async def matcher_handle():
            print(box.group, box.group.group_id)
    ```
    '''

    def __init__(self, name) -> None:
        self.name = name

    @property
    def group(self):
        '''box当前正在处理的群组

        仅可在matcher.handle装饰器注册的回调函数中访问
        '''
        event = current_event.get()
        if isinstance(event, GroupMessageEvent):
            return get_group(event.group_id)
        raise Exception("仅当处理群聊消息时可用")

    @property
    def state(self):
        '''box当前正在处理的群组的状态

        仅可在matcher.handle装饰器注册的回调函数中访问
        '''
        return self.group.state

    @property
    def cache(self):
        '''box的缓存

        仅可在matcher.handle装饰器注册的回调函数中访问
        '''
        return self.group.cache[self.name]

    def set_state(self, state: Union[str, AyakaState] = root_state):
        '''修改当前群组状态

        参数: 
            state: 新状态，为空时设置群组状态为根状态

        示例代码1:
        ```
            # 设置状态为 根状态.test

            @matcher.handle()
            async def matcher_handle():
                box.set_state("test") 
        ```

        示例代码2:
        ```
            # 设置状态为 根状态

            @matcher.handle()
            async def matcher_handle(): 
                box.set_state()  
        ```
        '''
        if isinstance(state, str):
            state = root_state.join(state)
        self.group.state = state

    def create_state_checker(self, *_states: Union[str, AyakaState], deep=0):
        '''返回一个检查state的checker

        参数:
            states: 注册状态，为空时匹配根状态
            deep: 可响应的子状态的最大深度

        返回:
            checker函数

        示例代码:
        ```
            from ayaka.box import AyakaBox
            from nonebot import on_message
            from nonebot.rule import Rule

            box = AyakaBox("测试")
            other_checkers = [...]

            matcher = on_message(rule=Rule(*other_checkers, box.create_state_checker("test")))
        ```
        '''
        if not _states:
            states = [root_state]
        else:
            states = [
                root_state.join(state) if isinstance(state, str) else state
                for state in _states
            ]

        def checker(event: GroupMessageEvent):
            group_state = get_group(event.group_id).state
            for state in states:
                _deep = group_state.belong(state)
                if _deep >= 0 and _deep <= deep:
                    return True
            return False

        return checker

    def create_cmd_matcher(self, cmds: list, states: list = [], deep: int = 0, **params):
        '''创建命令matcher

        参数:
            cmds: 注册命令
            states: 注册状态，为空时匹配根状态
            deep: 可响应的子状态的最大深度
            params: 其他参数，参考nonebot.on_command

        返回:
            nonebot.matcher.Matcher对象

        示例代码:
        ```
            from ayaka.box import AyakaBox
            from nonebot.rule import Rule

            box = AyakaBox("测试")

            def other_checker():
                ...

            matcher = box.create_cmd_matcher(
                cmds=["hh"], states=["test"], rule=Rule(other_checker))

            @matcher.handle()
            async def matcher_handle():
                ...
        ```
        '''
        rule = Rule(self.create_state_checker(
            *states, deep=deep)) & params.pop("rule", None)
        return on_command(cmd=tuple(cmds), rule=rule, **params)

    def create_text_matcher(self, states: list = [], deep: int = 0, **params):
        '''创建消息matcher

        参数:
            states: 注册状态，为空时匹配根状态
            deep: 可响应的子状态的最大深度
            params: 其他参数，参考nonebot.on_message

        返回:
            nonebot.matcher.Matcher对象
        '''
        rule = Rule(self.create_state_checker(
            *states, deep=deep)) & params.pop("rule", None)
        return on_message(rule=rule, **params)

    def remove_data_from_cache(self, key_or_obj: Union[str, T_BaseModel]):
        '''从当前群组的缓存移除指定的键-值对

        参数:
            key: 键名或BaseModel对象，如果是BaseModel对象，则自动取其类的名字作为键名

        示例代码:
        ```
            from pydantic import BaseModel
            from ayaka.box import AyakaBox

            box = AyakaBox("测试")
            matcher = box.create_text_matcher()

            class Data(BaseModel):
                cnt: int = 0

            @matcher.handle()
            async def matcher_handle():
                data = box.load_data_from_cache(Data)
                print(box.cache)
                box.remove_data_from_cache(data)
                print(box.cache)
        ```
        '''
        if isinstance(key_or_obj, str):
            key = key_or_obj
        elif isinstance(key_or_obj, BaseModel):
            key = key_or_obj.__class__.__name__
        else:
            raise Exception("参数类型错误，必须是字符串或BaseModel对象")
        self.cache.pop(key, None)

    def load_data_from_cache(self, cls: Type[T_BaseModel], key: str = None) -> T_BaseModel:
        '''从当前群组的缓存中加载指定的BaseModel对象

        参数:
            cls: BaseModel类
            key: 键名，为空时使用cls.__name__作为键名

        返回:
            BaseModel对象

        示例代码:
        ```
            from pydantic import BaseModel
            from ayaka.box import AyakaBox

            box = AyakaBox("测试")
            matcher = box.create_text_matcher()

            class Data(BaseModel):
                cnt: int = 0

            @matcher.handle()
            async def matcher_handle():
                data = box.load_data_from_cache(Data)
                data.cnt += 1
                print(data.cnt)
        ```
        '''
        if key is None:
            key = cls.__name__
        if key not in self.cache:
            data = cls()
            self.cache[key] = data
            return data
        return self.cache[key]
