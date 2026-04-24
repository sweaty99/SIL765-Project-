"""
Modern TLS client (educational)

Usage:
  python3 client_modern.py <host> <port>

This client requires TLS 1.2+ and prints the negotiated TLS version and cipher.
"""

import sys
import socket
import ssl


def connect(host, port):
    context = ssl.create_default_context()
    # Require TLS 1.2 or newer
    try:
        context.minimum_version = ssl.TLSVersion.TLSv1_2
    except AttributeError:
        pass

    # For demo we accept the self-signed cert (do NOT do this in production)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    with socket.create_connection((host, int(port))) as sock:
        with context.wrap_socket(sock, server_hostname=host) as ssock:
            print("Connected to", (host, port))
            print("Negotiated protocol:", ssock.version())
            print("Cipher:", ssock.cipher())
            ssock.sendall(b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n")
            data = ssock.recv(4096)
            print("Response (truncated):", data[:200])


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python3 client_modern.py <host> <port>")
        sys.exit(2)
    connect(sys.argv[1], sys.argv[2])
