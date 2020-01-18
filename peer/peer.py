#!/usr/bin/env python3

import asyncio as aio
import aioconsole

import signal
import sys

from ipaddress import ip_address
from typing import cast, List, Tuple

from client import ClientProtocol
from server import ServerProtocol
from control import ControlServerProtocol

cancel_signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)


def extract_ip_port(socket: str):
    ip, sep, port = socket.rpartition(":")
    assert sep
    ip = ip.strip("[]")
    return ip, port


async def main() -> None:
    ip_s, port_s = extract_ip_port(sys.argv[1])
    ip_c, port_c = extract_ip_port(sys.argv[2])
    ip_a, port_a = extract_ip_port(sys.argv[3])

    loop = aio.get_running_loop()

    task_server  = aio.ensure_future(ServerProtocol.serve(ip_s, int(port_s)))
    task_control = aio.ensure_future(ControlServerProtocol.serve(ip_a, int(port_a)))
    task_client1 = ClientProtocol.connect_to(ip_c, int(port_c))
    task_client2 = ClientProtocol.connect_to(ip_c, int(port_c) + 1)

    tasks = aio.gather(task_server, task_client1, task_client2, task_control)
    for s in cancel_signals:
        loop.add_signal_handler(s, tasks.cancel)
    try:
        await tasks
    except aio.CancelledError:
        print("Shutdown successful.")


if __name__ == "__main__":
    aio.run(main())
