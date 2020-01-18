#!/usr/bin/env python3

import asyncio as aio
import aioconsole

import signal
import sys

from ipaddress import ip_address
from typing import cast, List, Tuple


cancel_signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)


class ServerProtocol(aio.Protocol):
    @classmethod
    async def serve(cls, ip: str, port: int) -> None:
        loop = aio.get_running_loop()
        server = await loop.create_server(cls, ip, port)
        addr = cast(List, server.sockets)[0].getsockname()
        print(f"Serving on {addr}")
        try:
            await server.serve_forever()
        except aio.CancelledError:
            await cls.shutdown(addr, loop)
            server.close()

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


class ClientProtocol(aio.Protocol):
    clients: List = []

    @staticmethod
    async def _listen_to_stdin(prtcl):
        try:
            while not prtcl.on_con_lost.done():
                print(">", end="")
                msg = await aioconsole.ainput()
                await prtcl.send_data(msg.encode())
        except EOFError:
            prtcl.on_con_lost.cancel()
        except Exception:
            raise aio.CancelledError

    @classmethod
    async def connect_to(cls, ip: str, port: int):
        loop = aio.get_running_loop()
        on_con_lost = loop.create_future()
        on_con_made = loop.create_future()

        print(ip, port)
        transport, protocol = await loop.create_connection(
            lambda: cls(on_con_lost, on_con_made), ip, port,
        )
        listener_to_stdin = aio.ensure_future(cls._listen_to_stdin(protocol))
        task = aio.gather(on_con_lost)
        try:
            await on_con_made
            print("con made to ")
            await task
            listener_to_stdin.cancel()
        except aio.CancelledError:
            print("Client shutdown successful.")
        finally:
            transport.close()

    def __init__(self, on_con_lost, on_con_made):
        self.on_con_lost = on_con_lost
        self.on_con_made = on_con_made
        self.__class__.clients.append(self)

    async def send_data(self, data: bytes):
        self.transport.write(data)
        # self.transport.close()

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


def extract_ip_port(socket: str):
    ip, sep, port = socket.rpartition(":")
    assert sep
    ip = ip.strip("[]")
    return ip, port


async def main() -> None:
    ip_s, port_s = extract_ip_port(sys.argv[1])
    ip_c, port_c = extract_ip_port(sys.argv[2])

    loop = aio.get_running_loop()
    task_server = aio.ensure_future(ServerProtocol.serve(ip_s, int(port_s)))
    task_client = ClientProtocol.connect_to(ip_c, int(port_c))

    tasks = aio.gather(task_server, task_client)
    for s in cancel_signals:
        loop.add_signal_handler(s, tasks.cancel)
    try:
        await tasks
    except aio.CancelledError:
        print("Shutdown successful.")


if __name__ == "__main__":
    aio.run(main())
