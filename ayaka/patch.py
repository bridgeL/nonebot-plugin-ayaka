'''存放一些让人抓狂的eval方法'''
from .helpers import Timer


def money_patch_PluginManager_load_plugin():
    '''money patch nonebot.plugin.manager PluginManager.load_plugin方法
    
    令nb导入插件时，统计导入时长'''
    from nonebot.plugin.manager import PluginManager
    origin_func = PluginManager.load_plugin

    def func(self, name):
        with Timer(name):
            return origin_func(self, name)

    PluginManager.load_plugin = func
