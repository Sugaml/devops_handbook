#!/usr/bin/env bash
set -euo pipefail
PORT="${REDIS_PORT:-6382}"

redis-cli -p "$PORT" PING

redis-cli -p "$PORT" ACL SETUSER handbook-reader on ">reader-secret" ~handbook:* +@read -@dangerous -@admin
redis-cli -p "$PORT" ACL SETUSER handbook-writer on ">writer-secret" ~handbook:* +@read +@write -@dangerous -@admin
redis-cli -p "$PORT" ACL SETUSER handbook-admin on ">admin-secret" allcommands allkeys

redis-cli -p "$PORT" ACL SETUSER default off

redis-cli -p "$PORT" ACL SAVE
redis-cli -p "$PORT" ACL LIST

echo "ACL configured on port $PORT"
