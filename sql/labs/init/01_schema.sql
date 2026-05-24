-- Handbook DevOps lab schema — loaded on first container start

CREATE TABLE environments (
    id          SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        TEXT NOT NULL,
    region      TEXT NOT NULL,
    tier        TEXT NOT NULL CHECK (tier IN ('nonprod', 'prod', 'dr')),
    UNIQUE (name, region)
);

CREATE TABLE services (
    id          SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    team        TEXT NOT NULL,
    criticality TEXT NOT NULL CHECK (criticality IN ('low', 'medium', 'high'))
);

CREATE TABLE hosts (
    id              INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    hostname        TEXT NOT NULL UNIQUE,
    environment_id  SMALLINT NOT NULL REFERENCES environments (id),
    ip_address      INET NOT NULL,
    role            TEXT NOT NULL,
    cpu_cores       SMALLINT NOT NULL CHECK (cpu_cores > 0),
    mem_gb          SMALLINT NOT NULL CHECK (mem_gb > 0),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE deployments (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    service_id      SMALLINT NOT NULL REFERENCES services (id),
    environment_id  SMALLINT NOT NULL REFERENCES environments (id),
    version         TEXT NOT NULL,
    status          TEXT NOT NULL CHECK (status IN ('pending', 'running', 'success', 'failed', 'rolled_back')),
    deployed_by     TEXT NOT NULL,
    started_at      TIMESTAMPTZ NOT NULL,
    finished_at     TIMESTAMPTZ
);

CREATE TABLE incidents (
    id              INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    service_id      SMALLINT NOT NULL REFERENCES services (id),
    environment_id  SMALLINT NOT NULL REFERENCES environments (id),
    severity        TEXT NOT NULL CHECK (severity IN ('sev3', 'sev2', 'sev1')),
    title           TEXT NOT NULL,
    opened_at       TIMESTAMPTZ NOT NULL,
    resolved_at     TIMESTAMPTZ
);

CREATE INDEX idx_deployments_service_env ON deployments (service_id, environment_id);
CREATE INDEX idx_deployments_started_at ON deployments (started_at DESC);
CREATE INDEX idx_incidents_opened_at ON incidents (opened_at DESC);
