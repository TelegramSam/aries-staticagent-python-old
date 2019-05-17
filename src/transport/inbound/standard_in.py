import asyncio
import sys

inbound_queue = asyncio.Queue()

async def start():
    loop = asyncio.get_event_loop()
    print("Listening on stdin")
    while True:
        msg = ''
        line = await loop.run_in_executor(None, sys.stdin.readline)
        while line != "\n":
            msg += line
            line = await loop.run_in_executor(None, sys.stdin.readline)
        if msg:
            await inbound_queue.put(msg) 

async def recv():
    return await inbound_queue.get()
