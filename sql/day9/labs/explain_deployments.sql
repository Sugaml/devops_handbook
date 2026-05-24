-- Day 9 lab: EXPLAIN query plans

EXPLAIN
SELECT *
FROM deployments
WHERE service_id = 1 AND environment_id = 2
ORDER BY started_at DESC
LIMIT 10;

EXPLAIN (ANALYZE, BUFFERS)
SELECT
    d.version,
    d.status,
    s.name AS service_name
FROM deployments d
JOIN services s ON s.id = d.service_id
WHERE d.started_at >= now() - interval '30 days'
ORDER BY d.started_at DESC;

EXPLAIN ANALYZE
SELECT status, COUNT(*)
FROM deployments
GROUP BY status;

-- After creating idx_deployments_status, re-run:
-- CREATE INDEX idx_deployments_status ON deployments (status);
