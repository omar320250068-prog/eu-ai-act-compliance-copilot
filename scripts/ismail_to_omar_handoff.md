# Ismail → Omar Hendawy: Compliance Rules Handoff

**From:** Mohamed Ismail (Database Integration & Compliance Researcher)
**To:** Omar Hendawy (Database Manager — PostgreSQL 16+ / Alembic)
**Date:** 2026-04-22
**Subject:** compliance_rules table — data deliverables ready for integration

---

## Section 1 — What Omar Receives From Ismail

Omar receives two files to populate the `compliance_rules` table:

| File | Description |
|------|-------------|
| `compliance_rules_data.json` | A single JSON array containing **24 structured EU AI Act rule objects** covering all four risk tiers: UNACCEPTABLE (6), HIGH (8), LIMITED (4), MINIMAL (6). Each object has fields mapping directly to the `compliance_rules` table columns. |
| `seed_compliance_rules.py` | An async Python script that reads the JSON file and upserts all rules into PostgreSQL using SQLAlchemy async ORM with `asyncpg`. Safe to re-run — uses `ON CONFLICT (rule_code) DO UPDATE`. |

Both files are in the `scripts/` directory.

---

## Section 2 — Pre-Requisites Omar Must Complete First

Before running the seeding script, complete these steps:

- [ ] **Apply the Alembic migration** `a1b2c3d4e5f6_add_compliance_rules_full_schema.py`
  - This migration automatically enables `uuid-ossp` and `btree_gin` extensions
  - It adds missing columns: `description`, `annex_ref`, `blocks_deployment`, `requires_documentation`, `remediation_text`, `updated_at`
  - It creates the `risk_tier_enum` PostgreSQL type
  - It creates the GIN index on `rule_tree`
  - Command: `alembic upgrade head`
- [ ] **Ensure the `.env` file** contains `DATABASE_URL` set to the docker-compose PostgreSQL connection string:
  ```
  DATABASE_URL=postgresql+asyncpg://omar_admin:kali2026@localhost:5432/compliance_db
  ```
- [ ] **Verify the table exists** and is empty (for first-time seeding):
  ```sql
  SELECT COUNT(*) FROM compliance_rules;
  -- Expected: 0
  ```
- [ ] **Install Python dependencies** if not already installed:
  ```bash
  pip install sqlalchemy[asyncio] asyncpg python-dotenv
  ```

---

## Section 3 — How to Run the Seeding Script

```bash
# Navigate to project root
cd "C:\Users\OMAR HINDAWY\Desktop\new Data_Base"

# Ensure environment is set (or use the .env file)
# The script automatically loads .env via python-dotenv

# Run the seeding script
python scripts/seed_compliance_rules.py
```

### Expected Successful Output

```
2026-04-22 22:00:01 INFO Loaded 24 rule(s) from compliance_rules_data.json
2026-04-22 22:00:02 INFO ─── Seeding Complete ───
2026-04-22 22:00:02 INFO   24 rules inserted (new)
2026-04-22 22:00:02 INFO   0 rules updated (existing)
2026-04-22 22:00:02 INFO   0 rules skipped (validation failure)
2026-04-22 22:00:02 INFO   24 total rules processed
2026-04-22 22:00:02 INFO Database engine disposed. Seeding script finished.
```

If you re-run the script, you will see the counts shift from "inserted" to "updated":

```
2026-04-22 22:05:01 INFO   0 rules inserted (new)
2026-04-22 22:05:01 INFO   24 rules updated (existing)
```

### If It Fails

If the script errors, it will automatically **rollback the entire transaction** — no partial data will be committed. Look for:

```
ERROR Transaction rolled back due to error
```

Common fixes: verify `DATABASE_URL`, confirm the migration was applied, check that PostgreSQL is running.

---

## Section 4 — Schema Verification Queries

Run these three queries in pgAdmin or DBeaver after seeding to confirm correctness.

### Query 1: Total Rule Count Per Tier

```sql
SELECT risk_tier, COUNT(*)
FROM compliance_rules
GROUP BY risk_tier
ORDER BY risk_tier;
```

**Expected output:**

| risk_tier      | count |
|----------------|-------|
| HIGH           | 8     |
| LIMITED        | 4     |
| MINIMAL        | 6     |
| UNACCEPTABLE   | 6     |

### Query 2: Verify GIN Index Exists

```sql
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'compliance_rules'
  AND indexname = 'ix_compliance_rules_rule_tree';
```

**Expected output:**

| indexname | indexdef |
|-----------|---------|
| ix_compliance_rules_rule_tree | CREATE INDEX ix_compliance_rules_rule_tree ON public.compliance_rules USING gin (rule_tree) |

### Query 3: Verify JSONB Query on Seeded Data

```sql
SELECT rule_code, title, risk_tier
FROM compliance_rules
WHERE rule_tree @> '{"conditions": [{"keyword": "social scoring"}]}'
  AND is_active = TRUE;
```

**Expected output:**

| rule_code | title | risk_tier |
|-----------|-------|-----------|
| RULE-003  | Social Scoring by Public Authorities | UNACCEPTABLE |

---

*End of handoff document. Contact Mohamed Ismail for any questions about the rule data structure or legal references.*
