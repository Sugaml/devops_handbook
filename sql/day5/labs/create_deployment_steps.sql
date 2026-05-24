-- Day 5 lab: DDL for deployment_steps

CREATE TABLE IF NOT EXISTS deployment_steps (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    deployment_id   BIGINT NOT NULL REFERENCES deployments (id) ON DELETE CASCADE,
    step_name       TEXT NOT NULL,
    step_order      SMALLINT NOT NULL CHECK (step_order > 0),
    status          TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'ok', 'failed')),
    started_at      TIMESTAMPTZ,
    finished_at     TIMESTAMPTZ,
    UNIQUE (deployment_id, step_order)
);

CREATE INDEX IF NOT EXISTS idx_deployment_steps_deploy
    ON deployment_steps (deployment_id);

COMMENT ON TABLE deployment_steps IS 'Pipeline steps for a deployment run';

-- Example seed (adjust deployment_id to an existing row)
INSERT INTO deployment_steps (deployment_id, step_name, step_order, status, started_at, finished_at)
SELECT
    d.id,
    step.step_name,
    step.step_order,
    step.status,
    d.started_at + (step.step_order - 1) * interval '1 min',
    d.started_at + step.step_order * interval '1 min'
FROM deployments d
CROSS JOIN (VALUES
    ('pull_image',  1, 'ok'),
    ('migrate_db',  2, 'ok'),
    ('roll_pods',   3, 'ok')
) AS step(step_name, step_order, status)
WHERE d.status = 'success'
LIMIT 1;
