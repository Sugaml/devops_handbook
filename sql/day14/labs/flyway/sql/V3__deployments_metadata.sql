ALTER TABLE deployments
ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}';

COMMENT ON COLUMN deployments.metadata IS 'CI context: git_sha, pipeline, run_id';
