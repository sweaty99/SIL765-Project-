"""
Simple analyzer for negotiation results (educational)

Given a small JSON-like log or direct input about negotiated TLS versions, this
script flags negotiations that ended up below TLS 1.2. For the demo we keep it
minimal: it accepts a version string on the command line and reports if it's
below TLS 1.2.

Usage:
  python3 analyzer.py "TLS 1.0"
"""

import sys


def is_weak(version_str: str) -> bool:
    # Very small heuristic: consider 'TLS 1.0' and 'TLS 1.1' weak
    return any(v in version_str for v in ['TLS 1.0', 'TLS 1.1', 'SSL 3.0', 'SSLv3'])


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 analyzer.py '<protocol version string>'")
        sys.exit(2)

    version = sys.argv[1]
    if is_weak(version):
        print(f"WEAK: Negotiated version {version} is below TLS 1.2")
    else:
        print(f"OK: Negotiated version {version}")


if __name__ == '__main__':
    main()
