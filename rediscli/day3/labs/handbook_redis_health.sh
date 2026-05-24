#!/usr/bin/env bash
# Day 3 challenge — exit 0 if Redis healthy and memory under 90% of maxmemory
set -euo pipefail
host="${REDIS_HOST:-127.0.0.1}"
port="${REDIS_PORT:-6379}"

if ! redis-cli -h "$host" -p "$port" PING | grep -q PONG; then
  echo "FAIL: PING"
  exit 1
fi

max=$(redis-cli -h "$host" -p "$port" INFO memory | awk -F: '/^maxmemory:/{print $2}' | tr -d '\r')
used=$(redis-cli -h "$host" -p "$port" INFO memory | awk -F: '/^used_memory:/{print $2}' | tr -d '\r')

if [[ "$max" == "0" ]]; then
  echo "OK: no maxmemory limit set"
  exit 0
fi

pct=$((used * 100 / max))
if (( pct >= 90 )); then
  echo "FAIL: memory ${pct}% of maxmemory (${used}/${max})"
  exit 1
fi

echo "OK: memory ${pct}% of maxmemory"
exit 0
