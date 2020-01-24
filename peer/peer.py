#!/usr/bin/env python3

import asyncio as aio

# import aioconsole

import signal
import sys
import concurrent

# from ipaddress import ip_address
# from typing import cast, List, Tuple

from client import ClientProtocol
from server import ServerProtocol
from control import ControlServerProtocol
import worker

cancel_signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)

loop = None


def extract_ip_port(socket: str):
    ip, sep, port = socket.rpartition(":")
    assert sep
    ip = ip.strip("[]")
    return ip, port


async def main() -> None:
    ip_s, port_s = extract_ip_port(sys.argv[1])
    ip_a, port_a = extract_ip_port(sys.argv[2])

    loop = aio.get_running_loop()

    with concurrent.futures.ThreadPoolExecutor() as pool:
        task_control = await loop.run_in_executor(
            pool, lambda: ControlServerProtocol.serve(ip_a, int(port_a))
        )
        task_server = await loop.run_in_executor(
            pool, lambda: ServerProtocol.serve(ip_s, int(port_s))
        )
    # server = worker.Worker(
    #     aio.new_event_loop(), ServerProtocol.serve(ip_s, int(port_s))
    # )

    tasks = aio.gather(task_server, task_control)
    for s in cancel_signals:
        loop.add_signal_handler(s, tasks.cancel)
    try:
        await tasks
    except aio.CancelledError:
        print("Shutdown successful.")

    for w in ControlServerProtocol.workers:
        w.loop.stop()
    for w in ControlServerProtocol.workers:
        try:
            w.loop.close()
        except RuntimeError:
            pass
    for w in ControlServerProtocol.workers:
        w.thread.join()


if __name__ == "__main__":
    aio.run(main())
