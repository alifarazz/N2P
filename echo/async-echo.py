#!/usr/bin/env python3

import socket
import asyncio

HOST: str = "127.0.0.1"
PORT: int = 10000


async def handle_echo(reader, writer) -> None:
    while True:
        data = await reader.read(10)
        if not data:
            break
        msg = data.decode()
        addr = writer.get_extra_info("peername")
        print(f"Received {msg!r} from {addr!r}")
        print(f"Send: {msg!r}")
        writer.write(data)
        await writer.drain()
    print(f"Closing connection: {addr!r}")
    writer.close()


async def main() -> None:
    server = await asyncio.start_server(handle_echo, HOST, PORT)
    addr = server.sockets[0].getsockname()
    print(f"Serving on {addr}")

    try:
        async with server:
            await server.serve_forever()
    except Exception:
        print("W: interrupt received, stopping…")


if __name__ == "__main__":
    asyncio.run(main())
