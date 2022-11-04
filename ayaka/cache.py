class AyakaCache:
    def __repr__(self) -> str:
        return str(self.__dict__)

    def __getattr__(self, name: str):
        return self.__dict__.get(name)

    def __setitem__(self, key, val):
        self.__dict__[key] = val
        return val
