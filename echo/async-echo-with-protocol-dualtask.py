#!/usr/bin/env python3

import asyncio
import signal
import sys
from typing import cast, List, Tuple

HOST: str = "127.0.0.1"
PORT: int = 10000
signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)


class EchoServerProtocol(asyncio.Protocol):
    name: Tuple[str, int]

    def connection_made(self, transport):
        self.name = transport.get_extra_info("peername")
        print(f"Connected client on {self.name}.")
        self.transport = transport

    def connection_lost(self, exc):
        # What should I do with exc?
        print(f"Connection {self.name} closed.")

    def data_received(self, data):
        msg: str = data.decode()
        print(f"Received: {msg} from {self.name}")
        print(f"Sendnig:  {msg} to   {self.name}")
        self.transport.write(data)


async def serve(id: str, port: int) -> None:
    addr: Tuple

    async def shutdown(loop: asyncio.AbstractEventLoop) -> None:
        """Cleanup tasks tied to the service's shutdown."""
        print(f"Worker {id} received signal, shutting down…")
        # loop.stop()
        # pending = asyncio.all_tasks()
        # asyncio.gather(*pending)
        print(f"Worker {id} shutdown.")

    loop = asyncio.get_running_loop()
    server = await loop.create_server(EchoServerProtocol, sys.argv[1], port)
    addr = cast(List, server.sockets)[0].getsockname()
    print(f"Serving on {addr}")
    try:
        await server.serve_forever()
    except asyncio.CancelledError:
        await shutdown(loop)


async def main() -> None:
    loop = asyncio.get_running_loop()
    task1 = asyncio.ensure_future(serve("s1", PORT))
    task2 = asyncio.ensure_future(serve("s2", PORT + 1))
    task = asyncio.gather(task1, task2)
    for s in signals:
        loop.add_signal_handler(s, task.cancel)
    try:
        await task
    except asyncio.CancelledError:
        print("Shutdown successful.")


if __name__ == "__main__":
    asyncio.run(main())
