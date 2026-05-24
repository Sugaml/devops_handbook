#!/usr/bin/env bash
# Day 13 lab: backup and restore drill
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SQL_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKUP_FILE="${TMPDIR:-/tmp}/handbook-lab-$(date +%Y%m%d-%H%M%S).dump"
RESTORE_DB="handbook_restore"

cd "$SQL_ROOT"

echo "==> Dumping handbook to $BACKUP_FILE"
docker compose exec -T db pg_dump -U handbook -Fc handbook > "$BACKUP_FILE"
ls -lh "$BACKUP_FILE"

echo "==> Creating restore database $RESTORE_DB"
docker compose exec db psql -U handbook -d postgres -c "DROP DATABASE IF EXISTS $RESTORE_DB;"
docker compose exec db psql -U handbook -d postgres -c "CREATE DATABASE $RESTORE_DB OWNER handbook;"

echo "==> Restoring"
docker compose exec -T db pg_restore -U handbook -d "$RESTORE_DB" --no-owner --no-acl < "$BACKUP_FILE"

echo "==> Row count comparison"
docker compose exec db psql -U handbook -d handbook -c "
SELECT 'handbook' AS db, 'deployments' AS tbl, COUNT(*) FROM deployments
UNION ALL SELECT 'handbook', 'hosts', COUNT(*) FROM hosts;
"
docker compose exec db psql -U handbook -d "$RESTORE_DB" -c "
SELECT 'handbook_restore' AS db, 'deployments' AS tbl, COUNT(*) FROM deployments
UNION ALL SELECT 'handbook_restore', 'hosts', COUNT(*) FROM hosts;
"

echo "==> Done. Backup kept at $BACKUP_FILE"
echo "    Teardown restore DB: docker compose exec db psql -U handbook -d postgres -c \"DROP DATABASE $RESTORE_DB;\""
