-- 002_create_assessments.sql
-- Stores AI-generated compliance assessment results

CREATE TYPE risk_tier AS ENUM (
    'UNACCEPTABLE',
    'HIGH',
    'LIMITED',
    'MINIMAL'
);

CREATE TABLE IF NOT EXISTS assessments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID        NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    risk_tier       risk_tier   NOT NULL,
    confidence_score NUMERIC(5,4) CHECK (confidence_score BETWEEN 0 AND 1),
    reasoning       TEXT,           -- Human-readable explanation from the AI model
    raw_model_output JSONB,         -- Full inference payload for auditability
    assessed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    model_version   VARCHAR(100)    -- e.g., 'llama3-lora-v1.2' — tracks which model produced this
);

COMMENT ON TABLE assessments IS 'AI model output — risk tier classification per project submission.';
COMMENT ON COLUMN assessments.raw_model_output IS 'Full JSON payload from the inference engine; retained for audit and model drift analysis.';
COMMENT ON COLUMN assessments.confidence_score IS 'Probability score (0.0000–1.0000) from the classification model.';
