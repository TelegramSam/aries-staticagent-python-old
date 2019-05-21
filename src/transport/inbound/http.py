from aiohttp import web
from transport.connection import Connection, ConnectionType

async def accept(loop, connection_queue, **kwargs):
    print('Starting http server on /indy ...')
    routes = [
        web.post('/indy', post_handle)
    ]
    app = web.Application()
    app['connection_queue'] = connection_queue
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    server = web.TCPSite(runner=runner, port=kwargs['port'])
    print('Starting on localhost:{}'.format(kwargs['port']))
    await server.start()

async def post_handle(request):
    msg = await request.read()
    conn = HTTPConnection(msg)
    await request.app['connection_queue'].put(conn)
    await conn.wait()
    if conn.new_msg:
        return web.Response(text=conn.new_msg)
    else:
        raise web.HTTPAccepted()

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
