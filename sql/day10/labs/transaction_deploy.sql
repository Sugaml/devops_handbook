-- Day 10 lab: transactional deploy update
-- Run inside BEGIN...COMMIT or ROLLBACK for practice

BEGIN;

UPDATE deployments
SET status = 'failed',
    finished_at = now()
WHERE id = (
    SELECT id FROM deployments WHERE status = 'running' ORDER BY started_at LIMIT 1
)
RETURNING id, version, status;

-- If deployment_steps exists:
-- INSERT INTO deployment_steps (deployment_id, step_name, step_order, status, finished_at)
-- SELECT id, 'rollback', 99, 'failed', now()
-- FROM deployments WHERE status = 'failed' ORDER BY finished_at DESC LIMIT 1;

-- COMMIT;
ROLLBACK;
