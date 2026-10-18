-- 003_create_compliance_rules.sql
-- Legal rule store for EU AI Act compliance logic
-- Hierarchical data stored as JSONB for flexibility + queryability

CREATE TABLE IF NOT EXISTS compliance_rules (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_code       VARCHAR(50) UNIQUE NOT NULL,   -- e.g., 'ART_6_1', 'ANNEX_III_8'
    title           VARCHAR(500) NOT NULL,
    risk_tier       risk_tier NOT NULL,             -- which risk tier this rule governs
    source_ref      VARCHAR(200),                   -- e.g., 'EU AI Act 2024, Article 6(1)'
    rule_tree       JSONB NOT NULL,                 -- Full hierarchical rule structure
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    effective_date  DATE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE compliance_rules IS 'Master legal rule registry seeded from EU AI Act. Hierarchical logic stored as JSONB.';
COMMENT ON COLUMN compliance_rules.rule_tree IS 
'Nested JSON representing rule logic. Example structure:
{
  "conditions": [
    {
      "field": "deployment_context",
      "operator": "in",
      "values": ["biometric_identification", "law_enforcement"],
      "sub_conditions": [
        {
          "field": "real_time",
          "operator": "equals",
          "values": [true]
        }
      ]
    }
  ],
  "outcome": "UNACCEPTABLE",
  "legal_basis": "Article 5(1)(a)"
}';
