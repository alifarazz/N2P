#!/usr/bin/env python3

import socket

HOST = '127.0.0.1'
PORT = 10000

def main() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        print(f'connected to {HOST}:{PORT}')
        s.sendall(b'Hell')
        data = s.recv(1024).decode('ascii')
        print(f'data received: {data}')


if __name__ == '__main__':
    main()
