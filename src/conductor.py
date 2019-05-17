import asyncio
from config import Config
from messages.message import Message
from messages.inbound_message import InboundMessage
from hooks import self_hook_point
import transport.inbound.standard_in as StdIn
import transport.outbound.standard_out as StdOut
from errors import UnknownTransportException

class Conductor:
    def __init__(self):
        self.wallet_handle = None
        self.inbound_transport = None
        self.outbound_transport = None

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
        asyncio.ensure_future(self.inbound_transport.start())

    async def recv(self):
        msg_bytes = await self.inbound_transport.recv()
        msg = await self.unpack(msg_bytes)
        return msg

    async def unpack(self, message: bytes):
        """ Perform processing to convert bytes off the wire to Message. """
        return Message.deserialize(message)

    async def send(self, to_key, from_key, msg):
        await self.outbound_transport.send(to_key, from_key, msg)
