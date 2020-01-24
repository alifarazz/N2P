#!/usr/bin/env python3

import asyncio as aio
import signal
import sys
import socket
import aioconsole

from typing import cast, List, Tuple

HOST: str = "127.0.0.1"
PORT: int = 10000
signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)


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


class EchoServerProtocol(aio.Protocol):
    name: Tuple[str, int]
    transport: socket.socket
    on_con_made: aio.Future

    def __init__(self, on_con_made):
        self.on_con_made = on_con_made

    def connection_made(self, transport):
        self.name = transport.get_extra_info("peername")
        print(f"Connected client on {self.name}.")
        self.transport = transport
        self.on_con_made.set_result(True)

    def connection_lost(self, exc):
        # What should I do with exc?
        print(f"Connection {self.name} closed.")

    def data_received(self, data):
        msg: str = data.decode()
        print(f"Received: {msg} from {self.name}")
        print(f"Sendnig:  {msg} to   {self.name}")
        self.transport.write(data)


async def main():
    loop = aio.get_event_loop()

    # Subscribers
    # TODO:
    #   - some cli for connecting to other servers.
    subscribers = []
    subscribers_task = aio.gather(*subscribers)

    # Server
    server = await loop.create_server(EchoServerProtocol(HOST, PORT))
    server_addr = cast(List, server.sockets)[0].getsockname()
    print(f"Serving on {addr}")

    task = aio.gather(server.serve_forever, subscribers_task)
    for s in signals:
        loop.add_signal_handler(s, task.cancel)

    try:
        await server.on_con_made
        await task
    except asyncio.CancelledError:
        print("Shutdown successful.")
    finally:
        [t.close() for t in subscribers]
        # server.close??


if __name__ == "__main__":
    aio.run(main())
