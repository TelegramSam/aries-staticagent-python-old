import aiohttp
from transport.connection import Connection, ConnectionType

class HTTPOutConnection(Connection):
    def __init__(self, endpoint):
        super().__init__(ConnectionType.SEND)
        self.endpoint = endpoint

    async def send(self, msg):
        async with aiohttp.ClientSession() as session:
            headers = {'content-type': 'application/ssi-agent-wire'}
            async with session.post(self.endpoint, data=msg, headers=headers) as resp:
                if resp.status != 202:
                    print(resp.status)
                    print(await resp.text())

async def open(**metadata):
    return HTTPOutConnection(metadata['their_endpoint'])
