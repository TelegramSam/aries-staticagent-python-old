""" Agent """
import asyncio
from contextlib import suppress
import logging

from compat import create_task
from config import Config
from errors import NoRegisteredRouteException, MessageProcessingFailed
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
        self.logger = None
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
        logging.getLogger().setLevel(logging.ERROR)
        agent.logger = logging.getLogger(__name__)
        agent.logger.setLevel(config.log_level)
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

    async def do_loop(self):
        msg = await self.conductor.recv()
        self.logger.debug('Handling Message: %s', msg.serialize())

        try:
            await self.handle(msg)
        except Exception as e:
            self.logger.exception(
                'Message processing failed\nMessage: %s\nError: %s',
                msg.serialize(),
                e
            )

            if self.config.halt_on_error:
                raise MessageProcessingFailed(
                    'Failed while processing message: {}'.format(msg.serialize())
                ) from e
        finally:
            self.logger.debug('Message handled: %s', msg.serialize())
            await self.conductor.message_handled()

    async def loop(self):
        if self.config.num_messages == -1:
            while True:
                await self.do_loop()
        else:
            for _ in range(0, self.config.num_messages):
                await self.do_loop()

    def route(self, msg_type):
        """ Register route decorator. """
        def register_route_dec(func):
            self.logger.debug('Setting route for agent %s\'s %s to %s', self.config.wallet, msg_type, func)
            self.routes[msg_type] = func
            return func

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

            # If no routes defined in module, attempt to route based on method matching
            # the message type name
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
