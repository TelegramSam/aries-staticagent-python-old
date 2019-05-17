""" Test Agent """
import asyncio
from collections import namedtuple
import pytest

from agent import Agent

MockMessage = namedtuple('MockMessage', ['type', 'test'])

@pytest.mark.asyncio
async def test_routing():
    """ Test that routing works in agent. """
    agent = Agent()

    called_event = asyncio.Event()

    @agent.route('testing_type')
    async def route_gets_called(agent, msg, **kwargs):
        kwargs['event'].set()

    test_msg = MockMessage('testing_type', 'test')
    await agent.handle(test_msg, event=called_event)

    assert called_event.is_set()
