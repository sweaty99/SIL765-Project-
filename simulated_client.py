"""
Simulated TLS client (plaintext demo)

This client sends a simple JSON 'ClientHello' to the simulated server and prints
the received 'ServerHello'. It then flags if the negotiated version is below
TLS 1.2 to demonstrate a downgrade outcome.

Usage:
  python3 simulated_client.py 127.0.0.1 5555
"""

import sys
import socket
import json


def main():
    if len(sys.argv) != 3:
        print('Usage: python3 simulated_client.py <host> <port>')
        sys.exit(2)

    host = sys.argv[1]
    port = int(sys.argv[2])

    # ClientHello: offer modern preferences first
    client_hello = {
        'versions': ['TLS 1.3', 'TLS 1.2', 'TLS 1.1', 'TLS 1.0'],
        'ciphers': ['TLS_AES_128_GCM_SHA256', 'TLS_CHACHA20_POLY1305_SHA256']
    }

    with socket.create_connection((host, port)) as sock:
        sock.sendall(json.dumps(client_hello).encode('utf-8'))
        data = sock.recv(4096).decode('utf-8')
        try:
            server_hello = json.loads(data)
        except Exception:
            print('Invalid server hello:', data)
            return
        print('ServerHello:', server_hello)

        ver = server_hello.get('selected_version', '')
        if ver in ('TLS 1.0', 'TLS 1.1', 'SSL 3.0'):
            print('ALERT: Negotiated a weak/legacy protocol:', ver)
        else:
            print('Negotiated protocol appears modern:', ver)


if __name__ == '__main__':
    main()
