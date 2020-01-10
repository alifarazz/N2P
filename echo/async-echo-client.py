#!/usr/bin/env python3

import asyncio as aio
import signal
import sys
import aioconsole

from typing import cast, Tuple


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

    def data_received(self, data):
        msg: str = data.decode()
        print(f"Received: {msg} from {self.name}")

    async def send_data(self, data):
        self.transport.write(data)
        # self.transport.close()


async def listen_to_stdin(protocol: EchoClientProtocol) -> None:
    # stdin, stdout = await aioconsole.get_standard_streams()
    try:
        while True:
            print("listining")
            msg = await aioconsole.ainput()
            await protocol.send_data(msg.encode())
    except Exception:
        raise aio.exceptions.CancelledError


async def main() -> None:
    loop = aio.get_running_loop()
    on_con_lost = loop.create_future()
    on_con_made = loop.create_future()

    transport, protocol = await loop.create_connection(
        lambda: EchoClientProtocol(on_con_lost, on_con_made),
        sys.argv[1],
        int(sys.argv[2]),
    )

    listener_to_stdin = aio.ensure_future(
        listen_to_stdin(cast(EchoClientProtocol, protocol))
    )

    task = aio.gather(listener_to_stdin, on_con_lost)
    for s in signals:
        loop.add_signal_handler(s, task.cancel)

    try:
        await on_con_made
        print("con made")
        await task
    except aio.exceptions.CancelledError:
        print("Shutdown successful.")
    finally:
        transport.close()


if __name__ == "__main__":
    aio.run(main())
