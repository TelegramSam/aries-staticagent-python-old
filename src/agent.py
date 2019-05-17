""" Agent """
import asyncio

from config import Config
from errors import NoRegisteredRouteException, UnknownTransportException
from hooks import self_hook_point
from messages.message import Message
from indy_sdk_utils import open_wallet
import transport.inbound.standard_in as StdIn
import transport.outbound.standard_out as StdOut

class Agent:
    """ Agent """
    hooks = {}

    def __init__(self):
        self.config = None
        self.wallet_handle = None
        self.inbound_transport = None
        self.outbound_transport = None
        self.routes = {}
        self.hooks = Agent.hooks.copy() # Copy statically configured hooks

    @staticmethod
    async def from_config(config: Config):
        agent = Agent()
        agent.config = config
        agent.wallet_handle = await open_wallet(
            agent.config.wallet,
            agent.config.passphrase,
            agent.config.ephemeral
        )

        # TODO: Better transport selection
        if not agent.config.inbound_transport == 'stdin':
            raise UnknownTransportException

        agent.inbound_transport = StdIn

        if not agent.config.outbound_transport == 'stdout':
            raise UnknownTransportException

        agent.outbound_transport = StdOut

        return agent

    async def start(self):
        asyncio.ensure_future(self.inbound_transport.start())
        while True:
            msg_bytes = await self.inbound_transport.recv()
            msg = await self.unpack(msg_bytes)
            await self.route(msg)


    def register_route(self, msg_type):
        """ Register route decorator. """
        def register_route_dec(func):
            self.routes[msg_type] = func

        return register_route_dec

    @self_hook_point()
    async def route(self, msg, *args, **kwargs):
        """ Route message """
        if not msg.type in self.routes:
            raise NoRegisteredRouteException

        await self.routes[msg.type](self, msg, *args, **kwargs)

    # Hooks discovered at runtime
    @self_hook_point()
    async def unpack(self, packed_message):
        """ Perform processing to convert bytes off the wire to Message. """
        return Message.deserialize(packed_message)
