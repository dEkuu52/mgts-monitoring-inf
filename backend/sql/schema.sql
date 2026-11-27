-- Canonical MGTS schema initializer. Safe to re-run for fresh and legacy databases.
CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    email       VARCHAR(255) NOT NULL UNIQUE,
    phone       VARCHAR(50),
    username    VARCHAR(100) NOT NULL UNIQUE,
    role        VARCHAR(50)  NOT NULL DEFAULT 'user',
    update_at   TIMESTAMP    NOT NULL DEFAULT NOW(),
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS statuses (
    id          SERIAL PRIMARY KEY,
    type        VARCHAR(100) NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS infrastructure_objects (
    id          SERIAL PRIMARY KEY,
    "imgUrl"    TEXT,
    type        VARCHAR(100),
    "statusId"  INTEGER REFERENCES statuses(id) ON DELETE SET NULL,
    place       TEXT
);

ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);
ALTER TABLE infrastructure_objects ADD COLUMN IF NOT EXISTS external_id VARCHAR(100);
ALTER TABLE infrastructure_objects ADD COLUMN IF NOT EXISTS lat DOUBLE PRECISION;
ALTER TABLE infrastructure_objects ADD COLUMN IF NOT EXISTS lon DOUBLE PRECISION;
ALTER TABLE infrastructure_objects ADD COLUMN IF NOT EXISTS processing_status VARCHAR(32);
ALTER TABLE infrastructure_objects ADD COLUMN IF NOT EXISTS processing_started_at TIMESTAMP;
ALTER TABLE infrastructure_objects ADD COLUMN IF NOT EXISTS processing_attempts INTEGER NOT NULL DEFAULT 0;
ALTER TABLE infrastructure_objects ADD COLUMN IF NOT EXISTS processing_error TEXT;
ALTER TABLE infrastructure_objects ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP;
ALTER TABLE infrastructure_objects ADD COLUMN IF NOT EXISTS processed_img_url TEXT;

CREATE INDEX IF NOT EXISTS infrastructure_objects_processing_status_idx
    ON infrastructure_objects (processing_status);

CREATE TABLE IF NOT EXISTS defects (
    id                  SERIAL PRIMARY KEY,
    object_id           INTEGER REFERENCES infrastructure_objects(id) ON DELETE SET NULL,
    detection_id        INTEGER,
    defect_type         VARCHAR(100) NOT NULL,
    defect_confidence   DOUBLE PRECISION,
    severity            VARCHAR(50),
    recommended_action  VARCHAR(50),
    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP NOT NULL DEFAULT NOW()
);

ALTER TABLE defects ADD COLUMN IF NOT EXISTS bbox JSONB;
ALTER TABLE defects ADD COLUMN IF NOT EXISTS source VARCHAR(20) NOT NULL DEFAULT 'manual';

CREATE INDEX IF NOT EXISTS defects_object_id_idx ON defects (object_id);
CREATE INDEX IF NOT EXISTS infrastructure_objects_status_id_idx ON infrastructure_objects ("statusId");

INSERT INTO statuses (type, description)
    SELECT 'unrecognized', 'Не распознано'
    WHERE NOT EXISTS (SELECT 1 FROM statuses WHERE type = 'unrecognized');
