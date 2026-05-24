-- Day 3 lab: ORDER BY, LIMIT, DISTINCT

SELECT version, status, started_at, finished_at
FROM deployments
ORDER BY started_at DESC
LIMIT 5;

SELECT hostname, cpu_cores, mem_gb
FROM hosts
ORDER BY mem_gb DESC, hostname ASC;

SELECT DISTINCT status FROM deployments ORDER BY status;

SELECT
    version,
    started_at,
    finished_at,
    finished_at - started_at AS duration
FROM deployments
WHERE finished_at IS NOT NULL
ORDER BY duration DESC;

SELECT DISTINCT ON (service_id)
    service_id, version, status, started_at
FROM deployments
ORDER BY service_id, started_at DESC;
