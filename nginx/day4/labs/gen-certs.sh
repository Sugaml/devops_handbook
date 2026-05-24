#!/usr/bin/env bash
# Generate self-signed TLS cert for handbook labs (Day 4+)
set -euo pipefail
DIR="$(cd "$(dirname "$0")/../../labs/certs" && pwd)"
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout "$DIR/handbook.key" \
  -out "$DIR/handbook.crt" \
  -subj "/CN=localhost/O=Handbook/C=US"
echo "Wrote $DIR/handbook.crt and handbook.key"
