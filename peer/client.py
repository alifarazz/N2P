import json
import re
import asyncio as aio
from typing import List, Dict

from msg_repo import MsgRepo
import server
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
        if not MsgRepo.is_broadcast_uuid_dup(uid):
            print(jsn)
            MsgRepo.mark_boradcast_uuid_as_seen(uid)
            ctrl_server.ControlServerProtocol.push_boradcast_msg(jsn["content"])
            server.ServerProtocol.relay(jsn)
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
            elif jsn["type"] == "S":
                regex = jsn["content"]["regex"]
                r = re.compile(regex)
                res = list(filter(r.match, MsgRepo.my_boradcast_contents))
                if res:
                    self.broadcast_answer(jsn, res[0])
                else:
                    server.ServerProtocol.relay_search(jsn)
            elif jsn["type"] == "A":
                try:
                    server.ServerProtocol.relay_answer(jsn)
                except Exception as e:
                    print(f"Error on relaying answer: {e.args}, ans:{jsn}")
            else:
                print(f"unsupported msg type, arrived at CLIENT: {self.name}\n{msg}")
        except KeyError:
            print(f"error on decoding json, CLIENT: {self.name}")
        except json.decoder.JSONDecodeError:
            print(f"error on decoding json, CLIENT: {self.name}")

    def broadcast_answer(self, jsn, result):
        hop_peer = jsn["content"]["hop-peer"]
        content_jsn = {
            "result": result,
            "hop-peer": hop_peer,
        }
        jsn = {"type": "A", "content": content_jsn}
        print(f"relay answer json: {jsn}")
        data = (json.dumps(jsn)).encode()
        self.transport.write(data)
        print("Answering done")