import asyncio as aio
from typing import cast, List


class ControlServerProtocol(aio.Protocol):
    # connection_lk = aio.Lock()

    @classmethod
    async def serve(cls, ip: str, port: int) -> None:
        loop = aio.get_running_loop()
        # on_con_lost = loop.create_future()
        server = await loop.create_server(cls, ip, port)
        addr = cast(List, server.sockets)[0].getsockname()
        print(f"Control Serving on {addr}")
        try:
            await server.start_serving()
            # await on_con_lost
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

    # def __init__(self, on_con_lost):
    #     # self.on_con_lost = on_con_lost
    #     super.__init__(self)

    # callback function
    def connection_made(self, transport):
        # if self.__class__.connection_lk.locked():
        #     if not self.on_con_lost.cancelled():
        #         self.on_con_lost.set_result(True)
        # self.__class__.connection_lk.acquire()
        self.name = transport.get_extra_info("peername")
        print(f"Connected client on {self.name}.")
        self.transport = transport

    # callback function
    def connection_lost(self, exc):
        # What should I do with exc?
        print(f"Connection {self.name} closed.")
        # self.__class__.connection_lk.acquire()
        # if not self.on_con_lost.cancelled():
        #     self.on_con_lost.set_result(True)

    # callback function
    def data_received(self, data):
        msg: str = data.decode()
        print(f"Received: {msg} from {self.name}")
        print(f"Sendnig:  {msg} to   {self.name}")
        self.transport.write(data)


