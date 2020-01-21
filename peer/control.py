import json
import time
import asyncio as aio
from typing import cast, List

from client import ClientProtocol
from server import ServerProtocol
from worker import Worker


class ControlServerProtocol(aio.Protocol):
    # connection_lk = aio.Lock()
    workers: List = []

    @classmethod
    async def serve(cls, ip: str, port: int) -> None:
        loop = aio.get_event_loop()
        # on_con_lost = loop.create_future()
        # cls.queue = janus.Queue(loop=loop)
        # ClientProtocol.queue = cls.queue
        server = await loop.create_server(cls, ip, port)
        addr = cast(List, server.sockets)[0].getsockname()
        print(f"Control Serving on {addr}")
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
        # if self.__class__.connection_lk.locked():
        #     if not self.on_con_lost.cancelled():
        #         self.on_con_lost.set_result(True)
        # self.__class__.connection_lk.acquire()
        self.name = transport.get_extra_info("peername")
        print(f"Connected admin on {self.name}.")
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
        loop = aio.get_running_loop()

        msg: str = data.decode()
        try:
            jsn = json.loads(msg)
            action = jsn["ACTION"]
            if action == "CONNECT":
                try:
                    ip, port = (jsn["IP"], int(jsn["PORT"]))
                    # coro = ClientProtocol.connect_to(ip, port)
                    # future = aio.run_coroutine_threadsafe(coro, loop)
                    print(f"Connecting to {ip}:{port}")
                    # future.result(2)  # 2 secs timeout
                    w = Worker(
                        aio.new_event_loop(), ClientProtocol.connect_to(ip, port)
                    )
                    self.__class__.workers.append(w)
                    # time.sleep(0.1)
                    self.transport.write(json.dumps({action: True}).encode())
                    print(f"Connected to {ip}:{port}")
                except Exception:
                    self.transport.write(json.dumps({action: False}).encode())
                    print(f"Connecting to {ip}:{port} failed.")
            elif action == "LIST":
                try:
                    print(ClientProtocol.clients.keys())
                    cc = [cid for cid in ClientProtocol.clients.keys()]
                    sc = list(ServerProtocol.transports.keys())
                    self.transport.write(
                        json.dumps({action: True, "SERVER": sc, "CLIENT": cc}).encode()
                    )
                    print(f"List of server: {sc}", f"List of clients: {cc}", sep="\n")
                except Exception:
                    self.transport.write(json.dumps({action: False}).encode())
                    print("Failed to list clients and server workers.")
            elif action == "KILL":
                try:
                    client_id = jsn["CLIENT-SOCKET"]
                    ClientProtocol.clients[client_id].transport.close()
                    self.transport.write(json.dumps({action: True}).encode())
                except Exception:
                    self.transport.write(json.dumps({action: False}).encode())
                    try:
                        print(f"Failed to kill client: {jsn['CLIENT-ID']}")
                    except json.decoder.JSONDecodeError:
                        print("Failed to kill client and bad CLIENT-ID.")
            elif action == "KILL-SERVER":
                try:
                    client_id = jsn["CLIENT-SOCKET"]
                    ServerProtocol.transports[client_id].close()
                    self.transport.write(json.dumps({action: True}).encode())
                    print(f"Killed client on server with clientid: {client_id}")
                except Exception:
                    self.transport.write(json.dumps({action: False}).encode())
                    try:
                        print(f"Failed to kill server's client: {jsn['CLIENT-ID']}")
                    except json.decoder.JSONDecodeError:
                        print("Failed to kill server's client and bad CLIENT-ID.")
            # elif action == "SEND":
            #     # ip, port = (jsn["IP"], int(jsn["PORT"]))
            #     try:
            #         client_id = jsn["CLIENT-SOCKET"]
            #         content = jsn["CONTENT"]
            #         ClientProtocol.clients[client_id].send_data_sync(content.encode())
            #         self.transport.write(json.dumps({action: True}).encode())
            #         print(f"Sent to client{client_id}")
            #     except Exception:
            #         self.transport.write(json.dumps({action: False}).encode())
            #         print(f"SEND error for client{client_id}")
            elif action == "BROADCAST":
                try:
                    content = jsn["CONTENT"]
                    for client_id in ServerProtocol.transports.keys():
                        transport = ServerProtocol.transports[client_id]
                        ServerProtocol.send_data_sync(
                            transport,
                            content.encode()
                        )
                        print(f"Sent to client {client_id}")
                    self.transport.write(json.dumps({action: True}).encode())
                except Exception:
                    self.transport.write(json.dumps({action: False}).encode())
                    print(f"SEND error for client {client_id}")
            else:
                self.transport.write(json.dumps({action: False}).encode())
                print("Action Not supported")
        except KeyError:
            print("error on decoding json")
        except json.decoder.JSONDecodeError:
            print("error on decoding json")
        # self.transport.write(data)

