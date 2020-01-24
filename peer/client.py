import json
import asyncio as aio
from typing import List, Dict

from msg_repo import MsgRepo
from server import ServerProtocol
import control as ctrl_server

# import aioconsole


class ClientProtocol(aio.Protocol):
    clients: Dict = {}

    # @staticmethod
    # async def _listen_to_stdin(prtcl):
    #     try:
    #         while not prtcl.on_con_lost.done():
    #             print(">", end="")
    #             msg = await aioconsole.ainput()
    #             await prtcl.send_data(msg.encode())
    #     except EOFError:
    #         prtcl.on_con_lost.cancel()
    #     except Exception:
    #         print("HACKety HACK HACK")
    #         raise aio.CancelledError

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
            await on_con_lost
        except aio.CancelledError:
            print("Client shutdown successful.")
        # finally:
        # transport.close()
        print("Client DONE")

    def __init__(self, on_con_lost, on_con_made):
        self.on_con_lost = on_con_lost
        self.on_con_made = on_con_made

    async def send_data(self, data: bytes):
        self.transport.write(data)

    def send_data_sync(self, data: bytes):
        self.transport.write(data)

    def connection_made(self, transport):
        self.name = transport.get_extra_info("peername")
        self.name = f"{self.name[0]}:{self.name[1]}"
        print(f"Connected to server on {self.name}.")
        self.transport = transport
        # self.transport.write(f"Hello from {self.name}".encode())
        self.__class__.clients[self.name] = self
        self.on_con_made.set_result(True)

    def connection_lost(self, exc):
        # What should I do with exc?
        print(f"Connection closed: {self.name} .")
        try:
            del self.__class__.clients[self.name]
        except KeyError:
            pass
        if not self.on_con_lost.cancelled():
            self.on_con_lost.set_result(True)

    def relay_broadcast_msg(self, jsn):
        uid = jsn["uuid"]
        print(jsn)
        if not MsgRepo.is_broadcast_uuid_dup(uid):
            MsgRepo.mark_uuid_as_seen(uid)
            ctrl_server.ControlServerProtocol.push_boradcast_msg(jsn["content"])
            ServerProtocol.relay(jsn)
        else:
            print(f"Client {self.name}: Duplicate msg yanked")

    def data_received(self, data: bytes):
        msg: str
        print("incoming")
        try:
            msg = data.decode()
        except Exception:
            print(f"error on decoding incoming data, CLIENT: {self.name}")
        # print(f"Received: {msg} from {self.name}")
        try:
            jsn = json.loads(msg)
            if jsn["type"] == "B":
                self.relay_broadcast_msg(jsn)
            else:
                print(f"unsupported msg type, arrived at CLIENT: {self.name}\n{msg}")
        except KeyError:
            print(f"error on decoding json, CLIENT: {self.name}")
        except json.decoder.JSONDecodeError:
            print(f"error on decoding json, CLIENT: {self.name}")

