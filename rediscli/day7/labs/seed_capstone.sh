#!/usr/bin/env bash
# Simulates a misbehaving deploy: huge session keys, no TTL, hot key
set -euo pipefail
PORT="${REDIS_PORT:-6383}"

redis-cli -p "$PORT" FLUSHDB

echo "Seeding session blobs..."
for i in $(seq 1 800); do
  blob=$(python3 -c "print('x'*50000)" 2>/dev/null || printf 'x%.0s' {1..50000})
  redis-cli -p "$PORT" SET "handbook:day7:session:$i" "$blob" >/dev/null
done

echo "Seeding hot key..."
for _ in $(seq 1 5000); do
  redis-cli -p "$PORT" INCR handbook:day7:hot:counter >/dev/null
done

echo "Normal checkout keys (with TTL)..."
redis-cli -p "$PORT" SET handbook:day7:checkout:ok cart42 EX 3600

echo "Slow pattern — many small keys without TTL..."
for i in $(seq 1 2000); do
  redis-cli -p "$PORT" HSET "handbook:day7:cart:$i" item "$i" price 9.99 >/dev/null
done

redis-cli -p "$PORT" INFO memory | grep -E 'used_memory_human|maxmemory'
redis-cli -p "$PORT" DBSIZE
echo "Seed complete. Begin investigation."
