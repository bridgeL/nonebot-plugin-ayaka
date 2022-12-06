from typing import List
from typing_extensions import Self


class AyakaChainNode:
    def __init__(self, key="", parent: Self = None):
        self.key = key
        self.parent = parent
        if not parent:
            self.keys = [key]
        else:
            self.keys = [*parent.keys, key]
        self.children: List[Self] = []

    def __getitem__(self, k):
        for node in self.children:
            if node.key == k:
                return node
        node = self.__class__(k, self)
        self.children.append(node)
        return node

    def __getattr__(self, k):
        return self[k]

    def __iter__(self):
        return iter(self.children)

    def __str__(self) -> str:
        return ".".join(self.keys)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self})"

    def dict(self):
        data = [child.dict() for child in self.children]
        return {
            "name": self.key,
            "children": data,
        }

    def join(self, *keys: str) -> Self:
        node = self
        for key in keys:
            node = node[key]
        return node

    def __gt__(self, node: Self):
        return self >= node and len(self.keys) > len(node.keys)

    def __ge__(self, node: Self):
        return self.belong(node)

    def __lt__(self, node: Self):
        return self <= node and len(self.keys) < len(node.keys)

    def __le__(self, node: Self):
        return node.belong(self)

    def __eq__(self, node: Self):
        return self <= node and len(self.keys) == len(node.keys)

    def belong(self, node: Self):
        if len(self.keys) < len(node.keys):
            return False

        for i in range(len(node.keys)):
            if node.keys[i] != self.keys[i]:
                return False

        return True
