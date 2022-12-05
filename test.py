class Test:
    def __init__(self) -> None:
        self.num = 10
        
    def __gt__(self, n:int):
        return self.num > n
    
    def __ge__(self, n:int):
        return self.num >= n
    
    def __lt__(self, n:int):
        return not self >= n
    
    def __le__(self, n:int):
        return not self.num > n

test = Test()

print(test > 2)
print(test >= 2)
print(test < 2)
print(test <= 2)

    