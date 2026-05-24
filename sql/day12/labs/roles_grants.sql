-- Day 12 lab: roles and grants (run as handbook superuser in lab)

CREATE ROLE oncall_ro LOGIN PASSWORD 'oncall-ro-lab' CONNECTION LIMIT 5;
CREATE ROLE ci_deploy LOGIN PASSWORD 'ci-deploy-lab' CONNECTION LIMIT 3;

GRANT CONNECT ON DATABASE handbook TO oncall_ro, ci_deploy;
GRANT USAGE ON SCHEMA public TO oncall_ro, ci_deploy;

GRANT SELECT ON environments, services, hosts, deployments, incidents TO oncall_ro;

GRANT SELECT, INSERT, UPDATE ON deployments TO ci_deploy;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ci_deploy;

CREATE OR REPLACE VIEW v_open_incidents AS
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
WHERE i.resolved_at IS NULL;

GRANT SELECT ON v_open_incidents TO oncall_ro;

-- Test as oncall_ro:
-- \c handbook oncall_ro
-- SELECT * FROM v_open_incidents LIMIT 3;
-- DELETE FROM deployments;  -- should fail
