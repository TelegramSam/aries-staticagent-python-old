""" Agent """
import asyncio

from conductor import Conductor
from config import Config
from errors import NoRegisteredRouteException, UnknownTransportException
from hooks import self_hook_point, hook
from messages.message import Message
from indy_sdk_utils import open_wallet

class Agent:
    """ Agent """
    hooks = {}

    def __init__(self):
        self.config = None
        self.wallet_handle = None
        self.conductor = None
        self.routes = {}
        self.hooks = Agent.hooks.copy() # Copy statically configured hooks
        self.main_task = None

    def hook(self, hook_name):
        return hook(self, hook_name)

    def register_hook(self, hook_name, hook_fn):
        hook(self, hook_name)(hook_fn)

    @staticmethod
    async def from_config(config: Config):
        agent = Agent()
        agent.config = config
        agent.wallet_handle = await open_wallet(
            agent.config.wallet,
            agent.config.passphrase,
            agent.config.ephemeral
        )
        return agent

    async def start(self):
        conductor_task = asyncio.create_task(self.conductor.start())
        main_loop = asyncio.create_task(self.loop())
        self.main_task = asyncio.gather(conductor_task, main_loop)
        await self.main_task

    async def shutdown(self):
        await self.conductor.shutdown()
        self.main_task.cancel()

    async def loop(self):
        if self.config.num_messages == -1:
            while True:
                msg = await self.conductor.recv()
                await self.handle(msg)
                await self.conductor.message_handled()
        else:
            for _ in range(0, self.config.num_messages):
                msg = await self.conductor.recv()
                await self.handle(msg)
                await self.conductor.message_handled()

    def route(self, msg_type):
        """ Register route decorator. """
        def register_route_dec(func):
            self.routes[msg_type] = func

        return register_route_dec

    # Hooks discovered at runtime
    @self_hook_point()
    async def handle(self, msg, *args, **kwargs):
        """ Route message """
        if not msg.type in self.routes:
            raise NoRegisteredRouteException

        await self.routes[msg.type](self, msg, *args, **kwargs)
