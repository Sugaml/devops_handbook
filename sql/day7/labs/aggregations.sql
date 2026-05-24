-- Day 7 lab: GROUP BY and window functions

SELECT role, COUNT(*) AS hosts, SUM(mem_gb) AS total_mem_gb
FROM hosts
GROUP BY role
ORDER BY hosts DESC;

SELECT status, COUNT(*) AS cnt
FROM deployments
GROUP BY status
ORDER BY cnt DESC;

SELECT
    e.name AS environment,
    COUNT(h.id) AS host_count
FROM environments e
LEFT JOIN hosts h ON h.environment_id = e.id
GROUP BY e.id, e.name
ORDER BY host_count DESC;

SELECT
    service_id,
    version,
    status,
    started_at,
    ROW_NUMBER() OVER (
        PARTITION BY service_id ORDER BY started_at DESC
    ) AS deploy_rank
FROM deployments;
