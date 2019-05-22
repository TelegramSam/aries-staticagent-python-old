import asyncio
from contextlib import suppress

from indy import crypto

from config import Config
from errors import UnknownTransportException
from hooks import self_hook_point
from messages.message import Message
import indy_sdk_utils as utils
import transport.inbound.standard_in as StdIn
import transport.outbound.standard_out as StdOut
import transport.inbound.http as HttpIn
import transport.outbound.http as HttpOut

class Conductor:
    hooks = {}
    def __init__(self):
        self.wallet_handle = None
        self.inbound_transport = None
        self.outbound_transport = None
        self.transport_options = {}
        self.connection_queue = asyncio.Queue()
        self.open_connections = {}
        self.message_queue = asyncio.Queue()
        self.hooks = Conductor.hooks.copy()
        self.async_tasks = []

    @staticmethod
    def in_transport_str_to_mod(transport_str):
        return {
            'stdin': StdIn,
            'http': HttpIn
        }[transport_str]

    @staticmethod
    def out_transport_str_to_mod(transport_str):
        return {
            'stdout': StdOut,
            'http': HttpOut,
        }[transport_str]

    @staticmethod
    def from_wallet_handle_config(wallet_handle, config: Config):
        conductor = Conductor()
        conductor.wallet_handle = wallet_handle
        conductor.transport_options = config.transport_options()

        try:
            conductor.inbound_transport = \
                    Conductor.in_transport_str_to_mod(config.inbound_transport)
            conductor.outbound_transport = \
                    Conductor.out_transport_str_to_mod(config.outbound_transport)
        except KeyError:
            raise UnknownTransportException

        return conductor

    def schedule_task(self, coro):
        task = asyncio.create_task(coro)
        self.async_tasks.append(task)

    async def start(self):
        inbound_task = asyncio.create_task(
            self.inbound_transport.accept(
                self.connection_queue,
                **self.transport_options
            )
        )
        accept_task = asyncio.create_task(self.accept())
        await asyncio.gather(inbound_task, accept_task)

    async def shutdown(self):
        await self.message_queue.join()
        for task in self.async_tasks:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

    async def accept(self):
        while True:
            conn = await self.connection_queue.get()
            self.schedule_task(self.message_reader(conn))

    async def message_reader(self, conn):
        async for msg_bytes in conn.recv():
            if not msg_bytes:
                continue

            msg = await self.unpack(msg_bytes)
            if not msg.context:
                # plaintext messages are ignored
                conn.close()
                continue

            self.message_queue.put_nowait(msg)
            if not msg.context['from_key']:
                # anonymous messages cannot be return routed
                conn.close()
                continue

            if not '~transport' in msg or 'return_route' not in msg['~transport']:
                if not conn.can_recv():
                    # Can't get any more messages and not marked as
                    # return_route so close
                    conn.close()
                # Connection thinks there are more messages so don't close
                continue

            self.open_connections[msg.context['from_key']] = conn
            self.schedule_task(self.connection_cleanup(conn, msg.context['from_key']))

    async def connection_cleanup(self, conn, conn_id):
        await conn.wait()
        del self.open_connections[conn_id]

    async def recv(self):
        msg = await self.message_queue.get()
        return msg

    async def message_handled(self):
        self.message_queue.task_done()

    @self_hook_point()
    async def unpack(self, message: bytes):
        """ Perform processing to convert bytes off the wire to Message. """
        return await utils.unpack(self.wallet_handle, message)

    async def send(self, to_did, to_key, from_key, msg):
        meta = await utils.get_did_metadata(self.wallet_handle, to_did)
        wire_msg = await crypto.pack_message(
            self.wallet_handle,
            msg.serialize(),
            [to_key],
            from_key
        )

        if to_key not in self.open_connections:
            conn = await self.outbound_transport.open(**meta)
        else:
            conn = self.open_connections[to_key]

        await conn.send(wire_msg)

        if not conn.closed() and conn.can_recv():
            self.schedule_task(self.message_reader(conn))
