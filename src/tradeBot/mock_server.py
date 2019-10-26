import json
from time import sleep

import random
import socket
import threading

from src.security.securityManager import SecurityManager


def mock_hello():
    return (json.dumps({
        "type": "hello",
        "symbols": [
            {"symbol": sec, "position": random.randint(0, 100)} for sec in SecurityManager.securities
        ],
    }) + "\n").encode('ascii')


def mock_open():
    num_open = random.randint(6, 7)
    secs = random.sample(SecurityManager.securities, k=num_open)
    return (json.dumps({
        "type": "open",
        "symbols": secs,
    }) + "\n").encode('ascii')


def mock_close():
    return (json.dumps({
        "type": "close",
    }) + "\n").encode('ascii')


def handler(sock, addr):
    print('Accept new connection from %s:%s...' % addr)
    while True:
        try:
            sock.send(mock_open())
            for i in range(100):
                # 100 ticks for 10 seconds
                sock.send(mock_hello())
                sleep(0.1)
            sock.send( mock_close())
            sleep(1.2)
        except ConnectionResetError or BrokenPipeError as e:
            break
    sock.close()

    print(f'Connection from {addr}:{addr} closed')


def main():
    s = socket.socket()
    s.bind(("localhost", 7778))
    s.listen(5)
    while True:
        sock, addr = s.accept()
        t = threading.Thread(target=handler, args=(sock, addr))
        t.start()
        pass


if __name__ == '__main__':
    main()
