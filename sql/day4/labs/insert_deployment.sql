-- Day 4 lab: INSERT and UPDATE (run inside BEGIN...ROLLBACK for practice)

INSERT INTO deployments (
    service_id, environment_id, version, status,
    deployed_by, started_at, finished_at
) VALUES (
    2, 1, '1.8.4-lab', 'success',
    'handbook-lab', now() - interval '2 hours', now() - interval '1 hour 58 min'
)
RETURNING id, version, status;

UPDATE deployments
SET status = 'success',
    finished_at = now()
WHERE status = 'running'
RETURNING id, version, status, finished_at;
