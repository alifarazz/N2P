#!/usr/bin/env python3

import socket
import asyncio
import signal
from typing import Tuple

HOST:str = '127.0.0.1'
PORT:int = 10000
signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)


class EchoProtocol(asyncio.Protocol):
    name:Tuple[str, int]

    def connection_made(self, transport):
        self.name = transport.get_extra_info('peername')
        print(f"Connected client on {self.name}.")
        self.transport = transport

    def connection_lost(self, exc):
        # What should I do with exc?
        print(f"Connection {self.name} closed.")

    def data_received(self, data):
        msg:str = data.decode()
        print(f"Received: {msg!r} from {self.name!r}")
        print(f"Sendnig:  {msg!r} to   {self.name!r}")
        self.transport.write(data)


async def serve() -> None:
    def shutdown(loop:asyncio.AbstractEventLoop) -> None:
        """Cleanup tasks tied to the service's shutdown."""
        print(f"Received exit signal, shutting down…")
        loop.stop()
        pending = asyncio.all_tasks()
        asyncio.gather(*pending)
        print("Shutdown complete.")

    loop = asyncio.get_running_loop()
    server = await loop.create_server(EchoProtocol, HOST, PORT)
    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')

    try:
        await server.serve_forever()
    except asyncio.CancelledError:
        shutdown(loop)


def main() -> None:
    loop = asyncio.get_event_loop()
    task = asyncio.ensure_future(serve())
    for s in signals:
        loop.add_signal_handler(s, task.cancel)
    try:
        loop.run_until_complete(task)
    finally:
        loop.close()


if __name__ == '__main__':
    main()
