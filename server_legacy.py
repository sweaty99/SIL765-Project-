"""
Legacy TLS server (educational)

This server intentionally only allows TLS 1.0 for demonstration purposes.
Do NOT run this on public networks. Only run locally to compare negotiation differences.

Run: python3 server_legacy.py
"""

import socket
import ssl
import pathlib

CERT = pathlib.Path(__file__).with_name("cert.pem")
KEY = pathlib.Path(__file__).with_name("key.pem")
HOST = '127.0.0.1'
PORT = 4444


def main():
    if not CERT.exists() or not KEY.exists():
        print("cert.pem/key.pem not found. Run generate_certs.sh in this directory first.")
        return

    # Important: this intentionally allows old TLS versions (unsafe in production)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    try:
        # Force TLS 1.0 only (educational)
        context.minimum_version = ssl.TLSVersion.TLSv1
        context.maximum_version = ssl.TLSVersion.TLSv1
    except AttributeError:
        # Older Python: best-effort, may not be able to force exactly TLS 1.0
        pass

    context.load_cert_chain(certfile=str(CERT), keyfile=str(KEY))

    bindsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    bindsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    bindsock.bind((HOST, PORT))
    bindsock.listen(5)
    print(f"Legacy TLS server listening on {HOST}:{PORT} (TLS 1.0 only) - DO NOT expose")

    while True:
        newsock, addr = bindsock.accept()
        try:
            with context.wrap_socket(newsock, server_side=True) as ssock:
                print(f"Connection from {addr}")
                print("Negotiated protocol:", ssock.version())
                print("Cipher:", ssock.cipher())
                data = ssock.recv(4096)
                print("Received (truncated):", data[:200])
                ssock.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK")
        except ssl.SSLError as e:
            print("SSL error while handling connection:", e)
            newsock.close()


if __name__ == '__main__':
    main()
