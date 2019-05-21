import asyncio
import sys
from transport.connection import Connection, ConnectionType

class StdConnection(Connection):
    def __init__(self, msg):
        super().__init__(ConnectionType.RECV)
        self.msg = msg

    async def recv(self):
        self.done.set()
        return self.msg

async def accept(loop, connection_queue):
    print("Accepting on stdin")
    while True:
        msg = ''
        line = await loop.run_in_executor(None, sys.stdin.readline)
        while line != '\n':
            msg += line
            line = await loop.run_in_executor(None, sys.stdin.readline)

        if msg:
            await connection_queue.put(StdConnection(msg))
