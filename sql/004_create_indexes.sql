-- 004_create_indexes.sql
-- B-Tree indexes for high-frequency relational lookups
-- Task 4.1 & Task 4.2 Combined

-- assessments: most common join — look up all assessments for a project
CREATE INDEX IF NOT EXISTS idx_assessments_project_id
    ON assessments(project_id);

-- assessments: filter by risk tier for reporting dashboards
CREATE INDEX IF NOT EXISTS idx_assessments_risk_tier
    ON assessments(risk_tier);

-- assessments: composite index for "all HIGH risk assessments for a project"
CREATE INDEX IF NOT EXISTS idx_assessments_project_risk
    ON assessments(project_id, risk_tier);

-- projects: lookup by submitter for user-specific report views
CREATE INDEX IF NOT EXISTS idx_projects_submitter_email
    ON projects(submitter_email);

-- projects: time-series ordering for dashboards
CREATE INDEX IF NOT EXISTS idx_projects_created_at
    ON projects(created_at DESC);

-- compliance_rules: primary lookup key
CREATE INDEX IF NOT EXISTS idx_compliance_rules_rule_code
    ON compliance_rules(rule_code);

-- compliance_rules: filter active rules only (used in every evaluation query)
CREATE INDEX IF NOT EXISTS idx_compliance_rules_active
    ON compliance_rules(is_active) WHERE is_active = TRUE;


-- GIN index for JSONB containment queries on compliance_rules.rule_tree
-- Enables operators: @>, ?, ?|, ?& on the rule_tree column
CREATE INDEX IF NOT EXISTS idx_compliance_rules_rule_tree_gin
    ON compliance_rules USING GIN (rule_tree);
