""" noop message """
from messages.message import Message

class Noop(Message):
    """ noop message """
    TYPE = 'did:none:0000000000000000/noop/1.0/noop'
    def __init__(self, **kwargs):
        return_route = kwargs.get('return_route', False)
        if not return_route:
            contents = {'@type': Noop.TYPE}
        else:
            contents = {'@type': Noop.TYPE, '~transport': {'return_route': 'all'}}

        super().__init__(contents)
