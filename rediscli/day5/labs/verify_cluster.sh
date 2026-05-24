#!/usr/bin/env bash
set -euo pipefail
cli() { redis-cli -c -p 7000 "$@"; }

echo "== CLUSTER INFO =="
cli CLUSTER INFO | grep cluster_state

echo "== SET/GET with redirects =="
cli SET handbook:day5:cluster ok
cli GET handbook:day5:cluster

echo "== Hash tag slot =="
cli CLUSTER KEYSLOT 'user:{42}:profile'
cli CLUSTER KEYSLOT 'user:{42}:cart'

echo "== CLUSTER NODES (first 5 lines) =="
cli CLUSTER NODES | head -5

echo "Done."
