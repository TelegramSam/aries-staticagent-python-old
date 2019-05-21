import asyncio
from config import Config
import indy_sdk_utils as utils
from messages.message import Message
from hooks import self_hook_point
import transport.inbound.standard_in as StdIn
import transport.outbound.standard_out as StdOut
from errors import UnknownTransportException

class Conductor:
    hooks = {}
    def __init__(self):
        self.wallet_handle = None
        self.inbound_transport = None
        self.outbound_transport = None
        self.connection_queue = asyncio.Queue()
        self.open_connections = {}
        self.message_queue = asyncio.Queue()
        self.loop = asyncio.get_event_loop()
        self.hooks = Conductor.hooks.copy()

    @staticmethod
    def from_wallet_handle_config(wallet_handle, config: Config):
        con = Conductor()
        con.wallet_handle = wallet_handle

        # TODO: Better transport selection
        if not config.inbound_transport == 'stdin':
            raise UnknownTransportException

        con.inbound_transport = StdIn

        if not config.outbound_transport == 'stdout':
            raise UnknownTransportException

        con.outbound_transport = StdOut
        return con

    async def start(self):
        asyncio.create_task(self.inbound_transport.accept(self.loop, self.connection_queue))
        asyncio.create_task(self.accept())

    async def accept(self):
        while True:
            conn = await self.connection_queue.get()
            msg = await self.unpack(await conn.recv())
            self.message_queue.put_nowait(msg)
            if not msg.context or not msg.context['from_key']:
                conn.close()
            else:
                self.open_connections[msg.context['from_key']] = conn

    async def recv(self):
        return await self.message_queue.get()

    @self_hook_point()
    async def unpack(self, message: bytes):
        """ Perform processing to convert bytes off the wire to Message. """
        return await utils.unpack(self.wallet_handle, message)

    async def send(self, to_key, from_key, msg):
        conn = await self.outbound_transport.open(self.loop)
        out = 'TO: ' + to_key
        out += '\nFROM: ' + from_key
        out += '\nBODY: ' + msg.serialize()
        await conn.send(out)
