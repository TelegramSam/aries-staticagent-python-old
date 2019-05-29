""" Agent """
import asyncio
from contextlib import suppress

from compat import create_task
from config import Config
from errors import NoRegisteredRouteException
from hooks import self_hook_point, hook
from indy_sdk_utils import open_wallet

class Agent:
    """ Agent """
    # TODO Move hook stuff into Hookable
    hooks = {}

    def __init__(self):
        self.hooks = Agent.hooks.copy() # Copy statically configured hooks

        self.config = None
        self.wallet_handle = None
        self.conductor = None

        self.routes = {}
        self.modules = {}

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
        conductor_task = create_task(self.conductor.start())
        main_loop = create_task(self.loop())
        self.main_task = asyncio.gather(conductor_task, main_loop)
        await self.main_task

    async def shutdown(self):
        await self.conductor.shutdown()
        self.main_task.cancel()
        with suppress(asyncio.CancelledError):
            await self.main_task

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

    def route_module(self, module_instance):
        self.modules[module_instance.PROTOCOL] = module_instance

    # Hooks discovered at runtime
    @self_hook_point()
    async def handle(self, msg, *args, **kwargs):
        """ Route message """
        if msg.type in self.routes:
            await self.routes[msg.type](self, msg, *args, **kwargs)
            return

        if msg.protocol in self.modules:
            module_instance = self.modules[msg.protocol]

            if hasattr(module_instance, 'routes'):
                await module_instance.routes[msg.type](module_instance, self, msg, *args, **kwargs)
                return

            if hasattr(module_instance, msg.short_type) and \
                    callable(getattr(module_instance, msg.short_type)):

                await getattr(module_instance, msg.short_type)(
                    module_instance,
                    self,
                    msg,
                    *args,
                    **kwargs
                )
                return

        raise NoRegisteredRouteException

    async def send(self, msg, to_key, **kwargs):
        return await self.conductor.send(msg, to_key, **kwargs)

    async def put_message(self, message):
        return await self.conductor.put_message(message)
