#!/usr/bin/env bash
set -euo pipefail
nodes=(
  "127.0.0.1:7000"
  "127.0.0.1:7001"
  "127.0.0.1:7002"
)

echo "Waiting for nodes..."
for n in "${nodes[@]}"; do
  host="${n%:*}"
  port="${n#*:}"
  for _ in $(seq 1 30); do
    if redis-cli -h "$host" -p "$port" PING 2>/dev/null | grep -q PONG; then
      break
    fi
    sleep 1
  done
done

echo "Creating cluster (3 masters, 0 replicas)..."
redis-cli --cluster create "${nodes[@]}" --cluster-replicas 0 --cluster-yes

echo "Cluster created."
redis-cli --cluster check 127.0.0.1:7000
