#!/usr/bin/env bash
# Skeleton investigation — run commands and fill capstone_report.md
set -euo pipefail
PORT="${REDIS_PORT:-6383}"

section() { echo; echo "=== $1 ==="; }

section "PING"
redis-cli -p "$PORT" PING

section "INFO server (version, uptime)"
redis-cli -p "$PORT" INFO server | grep -E 'redis_version|uptime_in_seconds'

section "INFO memory"
redis-cli -p "$PORT" INFO memory | grep -E 'used_memory_human|maxmemory|mem_fragmentation_ratio'

section "INFO stats (hits, evictions, ops)"
redis-cli -p "$PORT" INFO stats | grep -E 'keyspace_hits|keyspace_misses|evicted_keys|instantaneous_ops_per_sec'

section "DBSIZE"
redis-cli -p "$PORT" DBSIZE

section "SLOWLOG (last 5)"
redis-cli -p "$PORT" SLOWLOG GET 5

section "Sample MEMORY USAGE"
redis-cli -p "$PORT" MEMORY USAGE handbook:day7:session:1 2>/dev/null || echo "key missing"
redis-cli -p "$PORT" MEMORY USAGE handbook:day7:hot:counter 2>/dev/null || true

section "SCAN count handbook:day7:session:* (first page)"
redis-cli -p "$PORT" SCAN 0 MATCH 'handbook:day7:session:*' COUNT 5

echo
echo "Next: redis-cli -p $PORT --bigkeys"
echo "Next: redis-cli -p $PORT --stat"
echo "Document findings in capstone_report.md"
