
"""[FastAPI](https://fastapi.tiangolo.com/) 驱动适配
"""

from fastapi import status, WebSocket


class FastAPIWebSocket:
    """FastAPI WebSocket Wrapper"""

    def __init__(self, websocket: WebSocket):
        self.websocket = websocket

    async def accept(self) -> None:
        await self.websocket.accept()

    async def close(
        self, code: int = status.WS_1000_NORMAL_CLOSURE, reason: str = ""
    ) -> None:
        await self.websocket.close(code)

    async def receive(self) -> str:
        return await self.websocket.receive_text()

    async def send(self, data: str) -> None:
        await self.websocket.send({"type": "websocket.send", "text": data})
