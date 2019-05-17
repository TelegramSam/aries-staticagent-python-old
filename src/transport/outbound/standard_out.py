import asyncio
import sys

loop = asyncio.get_event_loop()

async def send(to_key, msg):
    await loop.run_in_executor(None, sys.stdout.write, to_key, msg)
