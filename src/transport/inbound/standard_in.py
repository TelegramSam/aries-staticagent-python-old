import asyncio
import sys
from transport.connection import Connection, ConnectionType

class StdConnection(Connection):
    def __init__(self, loop):
        super().__init__(ConnectionType.RECV)
        self.loop = loop

    async def recv(self):
        while True:
            msg = ''
            line = await self.loop.run_in_executor(None, sys.stdin.readline)
            while line != '\n':
                msg += line
                line = await self.loop.run_in_executor(None, sys.stdin.readline)

            if msg:
                self.close()
                yield msg

async def accept(loop, connection_queue):
    print("Accepting on stdin")
    await connection_queue.put(StdConnection(loop))
