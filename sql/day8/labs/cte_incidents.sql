-- Day 8 lab: CTEs and EXISTS

WITH open_incidents AS (
    SELECT
        i.id,
        i.title,
        i.severity,
        s.name AS service_name,
        e.name AS environment_name,
        i.opened_at
    FROM incidents i
    JOIN services s ON s.id = i.service_id
    JOIN environments e ON e.id = i.environment_id
    WHERE i.resolved_at IS NULL
)
SELECT * FROM open_incidents ORDER BY opened_at DESC;

WITH failed_by_service AS (
    SELECT service_id, COUNT(*) AS failures
    FROM deployments
    WHERE status IN ('failed', 'rolled_back')
    GROUP BY service_id
)
SELECT s.name, COALESCE(f.failures, 0) AS failure_count
FROM services s
LEFT JOIN failed_by_service f ON f.service_id = s.id
ORDER BY failure_count DESC, s.name;

SELECT s.name
FROM services s
WHERE NOT EXISTS (
    SELECT 1 FROM deployments d WHERE d.service_id = s.id
);
