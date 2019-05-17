import asyncio
import sys

loop = asyncio.get_event_loop()

async def send(to_key, from_key, msg):
    out = "To: " + to_key
    out += "\nFrom: " + from_key
    out += "\nBody: " + msg.serialize()

    await loop.run_in_executor(None, print, out)
