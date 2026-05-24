-- Day 1 lab: basic SELECT

SELECT name, region, tier FROM environments;

SELECT id, name, team, criticality FROM services;

SELECT hostname, role, cpu_cores, mem_gb FROM hosts;

SELECT version, status, deployed_by, started_at
FROM deployments
ORDER BY started_at DESC
LIMIT 5;
