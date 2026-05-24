#!/usr/bin/env bash
set -euo pipefail
PORT="${REDIS_PORT:-6382}"

echo "== Writer SET =="
redis-cli -p "$PORT" --user handbook-writer -a writer-secret SET handbook:day6:token abc

echo "== Reader GET =="
redis-cli -p "$PORT" --user handbook-reader -a reader-secret GET handbook:day6:token

echo "== Reader SET (should fail) =="
if redis-cli -p "$PORT" --user handbook-reader -a reader-secret SET handbook:day6:fail x 2>&1 | grep -qi noperm; then
  echo "OK: reader denied write"
else
  echo "WARN: expected NOPERM"
fi

echo "== FLUSHALL disabled =="
if redis-cli -p "$PORT" --user handbook-admin -a admin-secret FLUSHALL 2>&1 | grep -qi unknown; then
  echo "OK: FLUSHALL renamed/disabled"
else
  echo "Note: FLUSHALL response may vary if rename not applied yet"
fi

echo "Done."
