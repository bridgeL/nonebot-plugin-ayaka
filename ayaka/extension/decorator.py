'''各种偷懒用的装饰器'''
from ..driver import get_driver
from ..utils import singleton


def run_in_startup(func):
    '''有时候我连get_driver都懒得写'''
    get_driver().on_startup(func)
    return func
