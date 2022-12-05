from pydantic import BaseModel


class Test(BaseModel):
    name: str
    age: int


print(Test.__annotations__)

line = "名字 123"
seperate = " "

# # 输入：
# line + seperate + Test

# # 输出
# test(test.name="名字", test.age=123)
