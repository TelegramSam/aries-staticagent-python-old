from module import module

@module
class Connect:
    DOC_URI = 'did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/'
    PROTOCOL = 'connection'
    VERSION = '1.0'

    async def invite(self, agent, msg, *args, **kwargs):
        pass

    async def request(self, agent, msg, *args, **kwargs):
        pass

    async def response(self, agent, msg, *args, **kwargs):
        pass
