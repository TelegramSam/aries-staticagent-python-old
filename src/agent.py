""" Agent """
from hooks import self_hook_point
from errors import NoRegisteredRouteException

class Agent:
    """ Agent """
    hooks = {}

    def __init__(self):
        self.routes = {}

        # Copy statically configured hooks
        self.hooks = Agent.hooks.copy()

    def register_route(self, msg_type):
        """ Register route decorator. """
        def register_route_dec(func):
            self.routes[msg_type] = func

        return register_route_dec

    async def route(self, msg, *args, **kwargs):
        """ Route message """
        if not msg.type in self.routes:
            raise NoRegisteredRouteException

        await self.routes[msg.type](msg, *args, **kwargs)

    async def deserialize(self, wire):
        """ Deserialization of message from bytes. """

    # Hooks discovered at runtime
    @self_hook_point('unpack')
    async def unpack(self, packed_message):
        """ Perform processing to convert bytes off the wire to Message. """
