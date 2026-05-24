-- Day 2 lab: WHERE filters

SELECT version, status, environment_id, started_at
FROM deployments
WHERE status IN ('failed', 'rolled_back', 'running');

SELECT hostname, role, mem_gb
FROM hosts
WHERE environment_id = 2 AND mem_gb >= 16;

SELECT title, severity, opened_at, resolved_at
FROM incidents
WHERE resolved_at IS NULL;

SELECT hostname
FROM hosts
WHERE hostname LIKE 'prod-%';
