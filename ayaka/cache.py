class AyakaCache(dict):
    def __getitem__(self, k):
        if k not in self:
            self[k] = AyakaCache()
        return super().__getitem__(k)

    def __getattr__(self, k):
        return self[k]

    def __setattr__(self, k, v):
        self[k] = v
