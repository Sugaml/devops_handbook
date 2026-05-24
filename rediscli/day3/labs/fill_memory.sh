#!/usr/bin/env bash
# Fill Redis until evictions — run with maxmemory=1mb and allkeys-lru
set -euo pipefail
host="${REDIS_HOST:-127.0.0.1}"
port="${REDIS_PORT:-6379}"
i=0
while redis-cli -h "$host" -p "$port" SET "handbook:day3:fill:$i" "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" >/dev/null; do
  i=$((i + 1))
  if (( i % 500 == 0 )); then
    echo "keys written: $i"
    redis-cli -h "$host" -p "$port" INFO stats | grep evicted_keys || true
  fi
  if (( i > 50000 )); then
    echo "safety stop"
    break
  fi
done
echo "done at $i keys"
