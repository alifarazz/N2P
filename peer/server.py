import time
import uuid
import re
import json
import asyncio as aio
from typing import cast, List, Dict

from msg_repo import MsgRepo

import control


class ServerProtocol(aio.Protocol):
    server = None
    transports: Dict = {}
    addr = None
    peername = None

    @classmethod
    async def serve(cls, ip: str, port: int) -> None:
        loop = aio.get_event_loop()
        cls.server = server = await loop.create_server(cls, ip, port)
        cls.addr = addr = cast(List, server.sockets)[0].getsockname()
        cls.peername = str(uuid.uuid4())
        print(f"Serving on {addr}")
        try:
            await server.serve_forever()
        except aio.CancelledError:
            await cls.shutdown(addr, loop)
            server.close()

    @classmethod
    def relay(cls, jsn):
        data = (json.dumps(jsn)).encode()
        for transport in cls.transports.values():  # add prints for clients
            cls.send_data_sync(transport, data)
        print("relaying done")

    @classmethod
    def broadcast(cls, content):
        uid = str(uuid.uuid4())
        src_name = f"{cls.addr[0]}:{cls.addr[1]}"
        content_jsn = {"text": content, "timestamp": int(time.time()), "srcp": src_name}
        jsn = {"uuid": uid, "type": "B", "content": content_jsn}
        MsgRepo.mark_boradcast_uuid_as_seen(uid)
        print(f"relay json: {jsn}")
        data = (json.dumps(jsn)).encode()
        for client_id in cls.transports.keys():
            transport = cls.transports[client_id]
            cls.send_data_sync(transport, data)
            print(f"Sent to client {client_id}")
        print("relaying done")

    @classmethod
    def search(cls, regex):
        r = re.compile(regex)
        res = list(filter(r.match, MsgRepo.my_boradcast_contents))
        if res:
            control.ControlServerProtocol.push_search_result(res[0])
        else:
            cls.broadcast_search(regex)

    @classmethod
    def broadcast_search(cls, regex):
        uid = str(uuid.uuid4())
        src_name = cls.peername
        content_jsn = {
            "regex": regex,
            "timestamp": int(time.time()),
            "hop-peer": [cls.peername],
        }
        jsn = {"uuid": uid, "type": "S", "content": content_jsn}
        MsgRepo.mark_boradcast_uuid_as_seen(uid)
        print(f"relay json: {jsn}")
        data = (json.dumps(jsn)).encode()
        for client_id in cls.transports.keys():
            transport = cls.transports[client_id]
            cls.send_data_sync(transport, data)
            print(f"Sent to client {client_id}")
        print("relaying done")

    @classmethod
    def relay_search(cls, jsn):
        try:
            if not MsgRepo.is_broadcast_uuid_dup(jsn["uuid"]):
                MsgRepo.mark_boradcast_uuid_as_seen(jsn["uuid"])
                regex = jsn["content"]["regex"]
                r = re.compile(regex)
                res = list(filter(r.match, MsgRepo.my_boradcast_contents))
                if res:
                    cls.boradcast_answer(jsn, res[0])
                else:
                    jsn["content"]["hop-peer"].append(cls.peername)
                    cls.relay(jsn)
            else:
                print(f"Client {cls.addr}, {cls.peername}: Duplicate search yanked")
        except Exception as e:
            print(f"Erro relaying search,\n{e.args}\n{jsn}")

    @classmethod
    def boradcast_answer(cls, jsn, result):
        hop_peer = jsn["content"]["hop-peer"]
        content_jsn = {
            "result": result,
            "hop-peer": hop_peer,
        }
        jsn = {"type": "A", "content": content_jsn}
        print(f"relay answer json: {jsn}")
        data = (json.dumps(jsn)).encode()
        for client_id in cls.transports.keys():
            transport = cls.transports[client_id]
            cls.send_data_sync(transport, data)
            print(f"Sent to answer client {client_id}")
        print("relaying answer done")

    @classmethod
    def relay_answer(cls, jsn):
        hop_peer = jsn["content"]["hop-peer"]

        if hop_peer[-1] != cls.peername:
            print(f"Ans not mine, not relyaing, intended for {hop_peer}")
            return None
        if len(hop_peer) == 1 and hop_peer[0] == cls.peername:
            control.ControlServerProtocol.push_search_result(jsn["content"]["result"])
            return None

        content_jsn = {
            "result": result,
            "hop-peer": hop_peer[:-1],
        }
        jsn = {"type": "A", "content": content_jsn}
        print(f"relay answer json: {jsn}")
        data = (json.dumps(jsn)).encode()
        for client_id in cls.transports.keys():
            transport = cls.transports[client_id]
            cls.send_data_sync(transport, data)
            print(f"Sent to answer client {client_id}")
        print("relaying answer done")

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
        pirnt("SHOULDN'T BE HAPPENING!!!")
        # print(f"Sendnig:  {msg} to   {self.name}")
        # self.transport.write(data)

