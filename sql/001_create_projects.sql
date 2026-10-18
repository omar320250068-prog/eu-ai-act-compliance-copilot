-- 001_create_projects.sql
-- Stores user-submitted AI project information for compliance assessment

CREATE TABLE IF NOT EXISTS projects (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(255)    NOT NULL,
    description TEXT            NOT NULL,
    submitter_email VARCHAR(320) NOT NULL,
    deployment_context VARCHAR(100) NOT NULL,  -- e.g., 'healthcare', 'education', 'law_enforcement'
    created_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- Auto-update updated_at on row modification
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_projects_updated_at
BEFORE UPDATE ON projects
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE projects IS 'User-submitted AI project records awaiting EU AI Act compliance assessment.';
COMMENT ON COLUMN projects.deployment_context IS 'High-level domain category — maps to EU AI Act Annex III risk sectors.';
