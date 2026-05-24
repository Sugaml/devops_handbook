#!/usr/bin/env bash
set -euo pipefail
PRIMARY_PORT="${PRIMARY_PORT:-6380}"
REPLICA_PORT="${REPLICA_PORT:-6381}"

echo "== Primary PING =="
redis-cli -p "$PRIMARY_PORT" PING

echo "== Replica PING =="
redis-cli -p "$REPLICA_PORT" PING

echo "== Write on primary =="
redis-cli -p "$PRIMARY_PORT" SET handbook:day4:verify "$(date -u +%Y-%m-%dT%H:%M:%SZ)"

sleep 1

echo "== Read on replica =="
val=$(redis-cli -p "$REPLICA_PORT" GET handbook:day4:verify)
echo "replica value: $val"

echo "== ROLE primary =="
redis-cli -p "$PRIMARY_PORT" ROLE | head -3

echo "== ROLE replica =="
redis-cli -p "$REPLICA_PORT" ROLE | head -3

echo "== Read-only check =="
if redis-cli -p "$REPLICA_PORT" SET handbook:day4:shouldfail x 2>&1 | grep -qi readonly; then
  echo "OK: replica rejected write"
else
  echo "WARN: expected READONLY error"
fi

echo "Done."
