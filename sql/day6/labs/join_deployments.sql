-- Day 6 lab: JOINs

SELECT
    d.id,
    d.version,
    d.status,
    s.name AS service_name,
    e.name AS environment_name,
    d.started_at
FROM deployments d
JOIN services s ON s.id = d.service_id
JOIN environments e ON e.id = d.environment_id
ORDER BY d.started_at DESC;

SELECT
    h.hostname,
    h.role,
    e.name AS environment,
    e.region
FROM hosts h
JOIN environments e ON e.id = h.environment_id
ORDER BY e.name, h.hostname;

SELECT
    s.name AS service,
    COUNT(d.id) AS deploy_count
FROM services s
LEFT JOIN deployments d ON d.service_id = s.id
GROUP BY s.id, s.name
ORDER BY deploy_count, s.name;
