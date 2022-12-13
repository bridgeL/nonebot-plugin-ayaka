'''计时'''

from time import time


class TimerMeta(type):
    def __getattr__(self, k):
        return Timer(k)


class Timer(metaclass=TimerMeta):
    def __init__(self, name) -> None:
        self.name = name

    def __enter__(self):
        self.time = time()

    def __exit__(self, a, b, c):
        diff = time() - self.time
        print(f"[{self.name}] 耗时{diff:.2f}s")
