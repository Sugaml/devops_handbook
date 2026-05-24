-- Day 11 lab: audit columns and JSONB metadata

ALTER TABLE deployments
ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}';

UPDATE deployments
SET metadata = metadata || jsonb_build_object(
    'git_sha', 'deadbeef',
    'pipeline', 'github-actions',
    'run_id', 12345
)
WHERE id = (SELECT id FROM deployments ORDER BY started_at DESC LIMIT 1);

SELECT version, status, metadata->>'git_sha' AS git_sha
FROM deployments
WHERE metadata ? 'git_sha';

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

ALTER TABLE services
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

DROP TRIGGER IF EXISTS services_updated_at ON services;
CREATE TRIGGER services_updated_at
BEFORE UPDATE ON services
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
