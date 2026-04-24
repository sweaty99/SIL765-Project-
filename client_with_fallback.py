"""
Client that simulates vulnerable fallback behavior (educational only)

This client first attempts a connection with TLS 1.2+. If the handshake fails, it
prints a log message and retries with progressively lower TLS minimums to simulate
an endpoint that silently falls back.

Usage:
  python3 client_with_fallback.py <host> <port>

Important: This is a demonstration of *client-side fallback behaviour* and
is NOT performing any interception or MITM. It highlights how falling back
can lead to negotiating weaker versions when the server allows them.
"""

import sys
import socket
import ssl
import time

FALLBACK_LEVELS = [
    ('TLSv1_2', ssl.TLSVersion.TLSv1_2),
    ('TLSv1_1', ssl.TLSVersion.TLSv1_1),
    ('TLSv1', ssl.TLSVersion.TLSv1),
]


def try_connect(host, port, min_version_name, min_version_enum):
    context = ssl.create_default_context()
    try:
        context.minimum_version = min_version_enum
    except Exception:
        pass

    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    try:
        with socket.create_connection((host, int(port)), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                print(f"Connected with minimum {min_version_name}; negotiated: {ssock.version()} | {ssock.cipher()}")
                ssock.sendall(b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n")
                data = ssock.recv(4096)
                print("Response (truncated):", data[:200])
                return True, ssock.version()
    except ssl.SSLError as e:
        print(f"Handshake failed with minimum {min_version_name}: {e}")
        return False, None
    except Exception as e:
        print(f"Connection error with minimum {min_version_name}: {e}")
        return False, None


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 client_with_fallback.py <host> <port>")
        sys.exit(2)

    host = sys.argv[1]
    port = sys.argv[2]

    for name, enum in FALLBACK_LEVELS:
        ok, negotiated = try_connect(host, port, name, enum)
        if ok:
            if negotiated and negotiated.startswith('TLS') and negotiated < 'TLS 1.2':
                print("ALERT: Negotiated version is weaker than TLS 1.2 (example downgrade).")
            return
        # Sleep to simulate retry/backoff behavior a vulnerable client might have
        time.sleep(0.5)

    print("All attempts failed. No connection established.")


if __name__ == '__main__':
    main()
