#!/usr/bin/env python3

import asyncio as aio
import aioconsole

import signal
import sys

from ipaddress import ip_address
from typing import cast, List, Tuple


class EchoServerProtocol(aio.Protocol):
    name: Tuple[str, int]

    @classmethod
    async def serve(cls, ip: str, port: int) -> None:
        loop = aio.get_running_loop()
        server = await loop.create_server(cls, ip, port)
        addr = cast(List, server.sockets)[0].getsockname()
        print(f'Serving on {addr}')
        try:
            await server.serve_forever()
        except aio.CancelledError:
            await cls.shutdown(addr, loop)

    @staticmethod
    async def shutdown(addr, loop: aio.AbstractEventLoop) -> None:
        """Cleanup tasks tied to the service's shutdown."""
        print(f"Worker {addr} received signal, shutting down…")
        # loop.stop()
        # pending = asyncio.all_tasks()
        # asyncio.gather(*pending)
        print(f"Worker {addr} shutdown.")

    # callback function
    def connection_made(self, transport):
        self.name = transport.get_extra_info("peername")
        print(f"Connected client on {self.name}.")
        self.transport = transport

    # callback function
    def connection_lost(self, exc):
        # What should I do with exc?
        print(f"Connection {self.name} closed.")

    # callback function
    def data_received(self, data):
        msg: str = data.decode()
        print(f"Received: {msg} from {self.name}")
        print(f"Sendnig:  {msg} to   {self.name}")
        self.transport.write(data)


class EchoClientProtocol(aio.Protocol):
    name: Tuple[str, int]
    on_con_lost: aio.Future
    on_con_made: aio.Future

    def __init__(self, on_con_lost, on_con_made):
        self.on_con_lost = on_con_lost
        self.on_con_made = on_con_made

    def connection_made(self, transport):
        self.name = transport.get_extra_info("peername")
        print(f"Connected to server on {self.name}.")
        self.transport = transport
        self.transport.write(f"Hello from {self.name}".encode())
        self.on_con_made.set_result(True)

    def connection_lost(self, exc):
        # What should I do with exc?
        print(f"Connection closed: {self.name} .")
        if not self.on_con_lost.cancelled():
            self.on_con_lost.set_result(True)

    def data_received(self, data: bytes):
        msg: str = data.decode()
        print(f"Received: {msg} from {self.name}")

    async def send_data(self, data: bytes):
        self.transport.write(data)
        # self.transport.close()


async def main() -> None:
    cancel_signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)

    ip, sep, port = sys.argv[1].rpartition(':')
    assert sep
    ip = ip.strip('[]')

    loop = aio.get_running_loop()
    task_server = aio.ensure_future(EchoServerProtocol.serve(ip, int(port)))

    tasks = aio.gather(task_server)
    for s in cancel_signals:
        loop.add_signal_handler(s, tasks.cancel)
    try:
        await tasks
    except aio.CancelledError:
        print("Shutdown successful.")


if __name__ == "__main__":
    aio.run(main())
