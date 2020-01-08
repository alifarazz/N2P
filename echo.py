#!/usr/bin/env python3

import socket
import asyncio

HOST: str = "127.0.0.1"
PORT: int = 10000


def handle_echo(s: socket.socket) -> None:
    s.listen()
    conn, addr = s.accept()
    with conn:
        print("Connected with", addr)
        while True:
            data = conn.recv(1024)
            if not data:
                break
            conn.sendall(data)


def main() -> None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT))
            print("socket bound")
            while True:
                handle_echo(s)
    except KeyboardInterrupt:
        print("W: interrupt received, stopping…")


if __name__ == "__main__":
    main()
