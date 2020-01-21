import asyncio as aio
import aioconsole
from typing import List


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
            print("HACKety HACK HACK")
            raise aio.CancelledError

    @classmethod
    async def connect_to(cls, ip: str, port: int):
        loop = aio.get_running_loop()
        on_con_lost = loop.create_future()
        on_con_made = loop.create_future()

        transport, protocol = await loop.create_connection(
            lambda: cls(on_con_lost, on_con_made), ip, port,
        )
        # listener_to_stdin = aio.ensure_future(cls._listen_to_stdin(protocol))
        task = aio.gather(on_con_lost)
        try:
            await on_con_made
            # await task
            # listener_to_stdin.cancel()
        except aio.CancelledError:
            print("Client shutdown successful.")
        # finally:
            # transport.close()
        print("DONE")

    def __init__(self, on_con_lost, on_con_made):
        self.on_con_lost = on_con_lost
        self.on_con_made = on_con_made

    async def send_data(self, data: bytes):
        self.transport.write(data)

    def send_data_sync(self, data: bytes):
        self.transport.write(data)


    def connection_made(self, transport):
        self.name = transport.get_extra_info("peername")
        print(f"Connected to server on {self.name}.")
        self.transport = transport
        self.transport.write(f"Hello from {self.name}".encode())
        self.__class__.clients.append(self)
        self.on_con_made.set_result(True)

    def connection_lost(self, exc):
        # What should I do with exc?
        print(f"Connection closed: {self.name} .")
        if not self.on_con_lost.cancelled():
            self.on_con_lost.set_result(True)

    def data_received(self, data: bytes):
        msg: str = data.decode()
        print(f"Received: {msg} from {self.name}")
