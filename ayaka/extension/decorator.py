'''各种偷懒用的装饰器'''
from ..driver import get_driver


def run_in_startup(func):
    '''有时候我连get_driver都懒得写'''
    get_driver().on_startup(func)
    return func


def singleton(cls):
    '''单例模式的装饰器'''
    instance = None

    def getinstance(*args, **kwargs):
        nonlocal instance
        if instance is None:
            instance = cls(*args, **kwargs)
        return instance

    return getinstance
