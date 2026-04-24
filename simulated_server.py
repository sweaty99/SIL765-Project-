"""
Simulated TLS server (plaintext demo)

This script mimics the ClientHello/ServerHello negotiation using a simple JSON
exchange over TCP. It is purely educational and does NOT perform TLS; use it
when the system TLS stack disallows old protocol versions but you want to
demonstrate negotiation and fallback behavior.

Usage:
  python3 simulated_server.py --mode legacy --port 5555

Modes:
- modern: server prefers TLS 1.2+ if client offers it.
- legacy: server selects TLS 1.0 if the client offers it.
"""

import argparse
import json
import socket

HOST = '127.0.0.1'


def pick_version(client_versions, mode):
    # client_versions is ordered from highest to lowest preference
    if mode == 'modern':
        for v in client_versions:
            if v in ('TLS 1.3', 'TLS 1.2'):
                return v
        return client_versions[0]
    else:  # legacy
        # If client offered TLS 1.0, pick it to simulate an old server
        if 'TLS 1.0' in client_versions:
            return 'TLS 1.0'
        return client_versions[-1]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--mode', choices=['modern', 'legacy'], default='modern')
    p.add_argument('--port', type=int, default=5555)
    args = p.parse_args()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((HOST, args.port))
        sock.listen(1)
        print(f"Simulated server listening on {HOST}:{args.port} mode={args.mode}")
        conn, addr = sock.accept()
        with conn:
            data = conn.recv(4096).decode('utf-8')
            try:
                client_hello = json.loads(data)
            except Exception:
                print('Invalid client hello:', data)
                return
            print('Received ClientHello:', client_hello)

            selected_version = pick_version(client_hello.get('versions', []), args.mode)
            selected_cipher = client_hello.get('ciphers', ['TLS_NULL'])[0]
            server_hello = {'selected_version': selected_version, 'selected_cipher': selected_cipher}
            conn.sendall(json.dumps(server_hello).encode('utf-8'))
            print('Sent ServerHello:', server_hello)


if __name__ == '__main__':
    main()
