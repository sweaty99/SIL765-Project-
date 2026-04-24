#!/usr/bin/env bash
# Simple script to generate a self-signed certificate for localhost
# Outputs: cert.pem, key.pem in the current directory

set -e

if [ -f cert.pem ] || [ -f key.pem ]; then
  echo "cert.pem or key.pem already exists in $(pwd). Remove them first if you want to regenerate."
  exit 1
fi

openssl req -x509 -nodes -newkey rsa:2048 \
  -keyout key.pem -out cert.pem -days 365 \
  -subj "/CN=localhost" >/dev/null 2>&1

echo "Generated cert.pem and key.pem"
