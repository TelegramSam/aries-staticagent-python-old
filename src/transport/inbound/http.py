import aiohttp
from transport.connection import Connection, ConnectionType

async def accept(loop, connection_queue, **kwargs):
    routes = [
        aiohttp.web.get('/indy', post_handle)
    ]
    app = aiohttp.web.Application()
    app['connection_queue'] = connection_queue
    app.add_routes(routes)
    runner = aiohttp.web.AppRunner(app)
    loop.run_until_complete(runner)
    server = aiohttp.web.TCPSite(runner=runner, port=kwargs['port'])
    await server.start()

async def post_handle(request):
    msg = await request.read()
    conn = HTTPConnection(msg)
    await request.app['connection_queue'].put(conn)
    await conn.wait()
    if conn.new_msg:
        return aiohttp.web.Response(text=conn.new_msg)
    else:
        raise aiohttp.web.HTTPAccepted()

class HTTPConnection(Connection):
    def __init__(self, msg):
        super().__init__(ConnectionType.RECV)
        self.msg = msg
        self.new_msg = None

    async def recv(self):
        self.set_send()
        yield self.msg

    async def send(self, new_msg):
        self.new_msg = new_msg
        self.close()
