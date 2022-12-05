from typing import Any, Dict, Optional
import sys
import asyncio


class ResultStore:
    _seq = 1
    _futures: Dict[int, asyncio.Future] = {}

    @classmethod
    def get_seq(cls) -> int:
        s = cls._seq
        cls._seq = (cls._seq + 1) % sys.maxsize
        return s

    @classmethod
    def add_result(cls, result: Dict[str, Any]):
        echo = result.get("echo")
        if not isinstance(echo, dict):
            return

        seq = echo.get("seq")
        if not isinstance(seq, int):
            return

        future = cls._futures.get(seq)
        if not future:
            return

        future.set_result(result)

    @classmethod
    async def fetch(
        cls, seq: int, timeout: Optional[float]
    ) -> Dict[str, Any]:
        future = asyncio.get_event_loop().create_future()
        cls._futures[seq] = future
        try:
            return await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            raise
        finally:
            del cls._futures[seq]
