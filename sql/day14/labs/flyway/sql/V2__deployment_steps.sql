-- V2: deployment_steps (idempotent for lab re-runs use IF NOT EXISTS)

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
