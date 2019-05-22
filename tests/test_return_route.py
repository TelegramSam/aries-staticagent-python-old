""" Test return routing. """

import pytest
import asyncio
import string
import random
from contextlib import suppress

import indy_sdk_utils as utils

from agent import Agent
from config import Config
from conductor import Conductor
from messages.message import Message

random.seed('testing_seed')

@pytest.fixture
def random_string_generator():
    def _random_string_generator(length):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    return _random_string_generator


@pytest.fixture
def config_factory(unused_tcp_port_factory, random_string_generator):
    def _config_factory():
        config = Config()
        config.wallet = random_string_generator(10)
        config.passphrase = random_string_generator(10)
        config.ephemeral = True
        config.inbound_transport = 'http'
        config.outbound_transport = 'http'
        config.port = unused_tcp_port_factory()
        config.num_messages = -1
        return config

    return _config_factory

@pytest.fixture
def agent_factory(config_factory):
    async def _agent_factory():
        config = config_factory()
        agent = await Agent.from_config(config)
        agent.conductor = Conductor.from_wallet_handle_config(agent.wallet_handle, config)
        return agent
    return _agent_factory

@pytest.fixture
def connect_agents():
    async def _connect_agents(a, b, **kwargs):
        a_did, a_vk = await utils.create_and_store_my_did(
            a.wallet_handle,
            seed = '0000000000000000000000000000000a'
        )
        b_did, b_vk = await utils.create_and_store_my_did(
            b.wallet_handle,
            seed = '0000000000000000000000000000000b'
        )
        await utils.store_their_did(a.wallet_handle, b_did, b_vk)
        await utils.set_did_metadata(
            a.wallet_handle,
            b_did,
            {'their_endpoint': 'http://localhost:{}/indy'.format(b.config.port)}
        )
        await utils.store_their_did(b.wallet_handle, a_did, a_vk)
        if 'client_server' not in kwargs:
            await utils.set_did_metadata(
                b.wallet_handle,
                a_did,
                {'their_endpoint': 'http://localhost:{}/indy'.format(a.config.port)}
            )
        return a_did, a_vk, b_did, b_vk
    return _connect_agents

@pytest.fixture
async def connected_agents(agent_factory, connect_agents):
    alice, bob = await agent_factory(), await agent_factory()
    alice_did, alice_vk, bob_did, bob_vk = await connect_agents(alice, bob)
    return (alice, alice_did, alice_vk, bob, bob_did, bob_vk)

@pytest.fixture
async def connected_client_server_agents(agent_factory, connect_agents):
    alice, bob = await agent_factory(), await agent_factory()
    alice_did, alice_vk, bob_did, bob_vk = await connect_agents(alice, bob, client_server=True)
    return (alice, alice_did, alice_vk, bob, bob_did, bob_vk)

@pytest.fixture
async def ping_pong_agents(connected_agents):
    (alice, alice_did, alice_vk, bob, bob_did, bob_vk) = connected_agents

    alice.ponged = asyncio.Event()

    @bob.route('ping')
    async def respond(agent, msg):
        print('got ping')
        pong = Message({'@type': 'pong'})
        await agent.conductor.send(
            msg.context['from_did'],
            msg.context['from_key'],
            msg.context['to_key'],
            pong
        )

    @alice.route('pong')
    async def got_pong(agent, msg):
        print('got pong')
        agent.ponged.set()

    gathered_agent_tasks = asyncio.gather(alice.start(), bob.start())

    yield (alice, alice_did, alice_vk, bob, bob_did, bob_vk)

    await alice.shutdown()
    await bob.shutdown()
    gathered_agent_tasks.cancel()
    with suppress(asyncio.CancelledError):
        await gathered_agent_tasks

@pytest.mark.asyncio
@pytest.mark.parametrize('message', [
    {'@type': 'ping', '~transport': {'return_route': 'all'}},
    {'@type': 'ping'}
])
async def test_http_return_route(ping_pong_agents, message):
    (alice, alice_did, alice_vk, bob, bob_did, bob_vk) = ping_pong_agents

    ping = Message(message)
    await alice.conductor.send(bob_did, bob_vk, alice_vk, ping)
    await asyncio.wait_for(alice.ponged.wait(), 20)
    assert alice.ponged.is_set()

@pytest.mark.asyncio
async def test_http_return_route_no_endpoint(connected_client_server_agents):
    (alice, alice_did, alice_vk, bob, bob_did, bob_vk) = connected_client_server_agents

    alice.ponged = asyncio.Event()

    @bob.route('ping')
    async def respond(agent, msg):
        print('got ping, sending pong should queue message')
        pong = Message({'@type': 'pong'})
        await agent.conductor.send(
            msg.context['from_did'],
            msg.context['from_key'],
            msg.context['to_key'],
            pong
        )
        print('sent pong to queue, probably')
        assert agent.conductor.queues[msg.context['from_key']].qsize() == 1

    @bob.route('noop')
    async def noop(agent, msg):
        pass

    @alice.route('pong')
    async def got_pong(agent, msg):
        print('got pong')
        agent.ponged.set()

    gathered_agent_tasks = asyncio.gather(alice.start(), bob.start())

    # No return route, can't respond directly
    ping = Message({'@type': 'ping'})
    await alice.conductor.send(bob_did, bob_vk, alice_vk, ping)

    print('sending noop to pump bob\'s queue')
    noop = Message({'@type': 'noop', '~transport': {'return_route': 'all'}})
    await alice.conductor.send(bob_did, bob_vk, alice_vk, noop)

    await asyncio.wait_for(alice.ponged.wait(), 5)
    assert alice.ponged.is_set()

    await alice.shutdown()
    await bob.shutdown()
    gathered_agent_tasks.cancel()
    with suppress(asyncio.CancelledError):
        await gathered_agent_tasks
