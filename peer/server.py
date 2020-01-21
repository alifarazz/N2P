import asyncio as aio
from typing import cast, List, Dict



class ServerProtocol(aio.Protocol):
    server = None
    transports: Dict = {}

    @classmethod
    async def serve(cls, ip: str, port: int) -> None:
        loop = aio.get_event_loop()
        cls.server = server = await loop.create_server(cls, ip, port)
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

    @staticmethod
    def send_data_sync(transport, data: bytes):
        transport.write(data)

    # callback function
    def connection_made(self, transport):
        self.name = transport.get_extra_info("peername")
        self.name = f"{self.name[0]}:{self.name[1]}"
        print(f"Connected client on {self.name}.")
        self.transport = transport
        self.__class__.transports[self.name] = transport

    # callback function
    def connection_lost(self, exc):
        # What should I do with exc?
        print(f"Connection {self.name} closed.")
        try:
            del self.__class__.transports[self.name]
        except KeyError:
            pass


    # callback function
    def data_received(self, data):
        msg: str = data.decode()
        print(f"Received: {msg} from {self.name}")
        print(f"Sendnig:  {msg} to   {self.name}")
        self.transport.write(data)

