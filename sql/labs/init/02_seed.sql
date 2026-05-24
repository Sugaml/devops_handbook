INSERT INTO environments (name, region, tier) OVERRIDING SYSTEM VALUE VALUES
    (1, 'staging',    'us-east-1', 'nonprod'),
    (2, 'production', 'us-east-1', 'prod'),
    (3, 'production', 'eu-west-1', 'prod'),
    (4, 'dr',         'us-west-2', 'dr');

SELECT setval(pg_get_serial_sequence('environments', 'id'), (SELECT MAX(id) FROM environments));

INSERT INTO services (name, team, criticality) VALUES
    ('payments-api',  'payments',  'high'),
    ('web-frontend',  'platform',  'medium'),
    ('batch-worker',  'data',      'low'),
    ('auth-service',  'security',  'high');

INSERT INTO hosts (hostname, environment_id, ip_address, role, cpu_cores, mem_gb) VALUES
    ('stg-web-01',    1, '10.0.1.10', 'web',    2,  4),
    ('stg-api-01',    1, '10.0.1.20', 'api',    4,  8),
    ('prod-web-01',   2, '10.1.1.10', 'web',    4,  16),
    ('prod-web-02',   2, '10.1.1.11', 'web',    4,  16),
    ('prod-api-01',   2, '10.1.2.20', 'api',    8,  32),
    ('prod-api-02',   2, '10.1.2.21', 'api',    8,  32),
    ('prod-worker-1', 2, '10.1.3.30', 'worker', 4,  16),
    ('eu-web-01',     3, '10.2.1.10', 'web',    4,  16),
    ('dr-api-01',     4, '10.9.2.20', 'api',    4,  16);

INSERT INTO deployments (service_id, environment_id, version, status, deployed_by, started_at, finished_at) VALUES
    (1, 1, '2.4.0', 'success',      'ci-bot',     now() - interval '5 days',  now() - interval '5 days' + interval '8 min'),
    (1, 2, '2.4.0', 'success',      'ci-bot',     now() - interval '4 days',  now() - interval '4 days' + interval '12 min'),
    (1, 2, '2.4.1', 'failed',       'ci-bot',     now() - interval '2 days',  now() - interval '2 days' + interval '3 min'),
    (1, 2, '2.4.1', 'rolled_back',  'oncall-alice', now() - interval '2 days' + interval '1 hour', now() - interval '2 days' + interval '1 hour 20 min'),
    (2, 1, '1.8.2', 'success',      'ci-bot',     now() - interval '3 days',  now() - interval '3 days' + interval '5 min'),
    (2, 2, '1.8.3', 'success',      'deploy-bob', now() - interval '1 day',   now() - interval '1 day' + interval '6 min'),
    (3, 2, '0.9.0', 'running',      'ci-bot',     now() - interval '30 min', NULL),
    (4, 2, '3.1.0', 'success',      'ci-bot',     now() - interval '6 hours', now() - interval '6 hours' + interval '10 min'),
    (4, 1, '3.0.9', 'success',      'ci-bot',     now() - interval '7 days',  now() - interval '7 days' + interval '9 min');

INSERT INTO incidents (service_id, environment_id, severity, title, opened_at, resolved_at) VALUES
    (1, 2, 'sev2', 'Elevated 5xx on payments-api', now() - interval '2 days', now() - interval '2 days' + interval '45 min'),
    (2, 2, 'sev3', 'CDN cache stale assets',       now() - interval '5 days', now() - interval '5 days' + interval '2 hours'),
    (1, 2, 'sev1', 'Payment processor timeout',    now() - interval '10 days', now() - interval '10 days' + interval '3 hours'),
    (4, 2, 'sev3', 'Auth token refresh latency',   now() - interval '1 day', NULL);
