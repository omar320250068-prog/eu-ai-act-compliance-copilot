"""Validates all Ismail deliverables — JSON data, seed script, migration, and ORM model."""
import json
import ast
import sys

def main():
    errors = 0

    # ── 1. Validate JSON ──────────────────────────────────────────────
    print("=" * 50)
    print("JSON VALIDATION: compliance_rules_data.json")
    print("=" * 50)
    try:
        with open("scripts/compliance_rules_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"  Total rules: {len(data)}")

        tiers = {}
        for r in data:
            t = r["risk_tier"]
            tiers[t] = tiers.get(t, 0) + 1

        for t in ["UNACCEPTABLE", "HIGH", "LIMITED", "MINIMAL"]:
            count = tiers.get(t, 0)
            status = "PASS" if count > 0 else "FAIL"
            print(f"  [{status}] {t}: {count} rules")
            if count == 0:
                errors += 1

        # Check required fields
        required = [
            "rule_id", "title", "description", "risk_tier",
            "legal_reference", "rule_tree", "blocks_deployment",
            "requires_documentation", "remediation_text", "effective_date",
        ]
        all_present = True
        for i, r in enumerate(data):
            for field in required:
                if field not in r:
                    print(f"  [FAIL] Rule {i} ({r.get('rule_id','?')}): missing '{field}'")
                    all_present = False
                    errors += 1
        if all_present:
            print(f"  [PASS] All {len(required)} required fields present in all {len(data)} rules")

    except Exception as e:
        print(f"  [FAIL] JSON load error: {e}")
        errors += 1

    # ── 2. Validate Python syntax ──────────────────────────────────────
    print()
    print("=" * 50)
    print("PYTHON SYNTAX VALIDATION (AST parse)")
    print("=" * 50)
    files = [
        "scripts/seed_compliance_rules.py",
        "alembic/versions/a1b2c3d4e5f6_add_compliance_rules_full_schema.py",
        "database/models.py",
    ]
    for filepath in files:
        try:
            with open(filepath, "r", encoding="utf-8") as fh:
                ast.parse(fh.read())
            print(f"  [PASS] {filepath}")
        except SyntaxError as e:
            print(f"  [FAIL] {filepath}: {e}")
            errors += 1

    # ── 3. Validate seed script structure ──────────────────────────────
    print()
    print("=" * 50)
    print("SEED SCRIPT STRUCTURAL CHECKS")
    print("=" * 50)
    with open("scripts/seed_compliance_rules.py", "r", encoding="utf-8") as fh:
        src = fh.read()

    checks = [
        ("BUG 1 FIX: No psycopg2 import", "psycopg2" not in src),
        ("BUG 1 FIX: Uses create_async_engine", "create_async_engine" in src),
        ("BUG 1 FIX: Uses AsyncSession", "AsyncSession" in src),
        ("BUG 2 FIX: Uses load_dotenv", "load_dotenv" in src),
        ("BUG 2 FIX: Uses os.environ", "os.environ" in src),
        ("BUG 2 FIX: No DB_CONFIG dict", "DB_CONFIG" not in src),
        ("BUG 3 FIX: Reads compliance_rules_data.json", "compliance_rules_data.json" in src),
        ("BUG 4 FIX: title validation check", "title" in src and "skip" in src.lower()),
        ("BUG 5 FIX: TIER_EFFECTIVE_DATES dict", "TIER_EFFECTIVE_DATES" in src),
        ("BUG 6 FIX: session.rollback()", "session.rollback()" in src),
        ("BUG 6 FIX: session.commit()", "session.commit()" in src),
        ("BUG 7 FIX: ComplianceRule ORM class", "class ComplianceRule" in src),
        ("BUG 8 FIX: No print() calls", src.count("print(") == 0),
        ("BUG 8 FIX: Uses logger.info", "logger.info" in src),
        ("BUG 8 FIX: Uses logger.warning", "logger.warning" in src),
        ("BUG 8 FIX: Uses logger.error", "logger.error" in src),
        ("BUG 8 FIX: logging.basicConfig", "logging.basicConfig" in src),
        ("BUG 9 FIX: async def seed_rules", "async def seed_rules" in src),
        ("BUG 9 FIX: asyncio.run()", "asyncio.run" in src),
        ("UPSERT: on_conflict_do_update", "on_conflict_do_update" in src),
    ]

    for name, passed in checks:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
        if not passed:
            errors += 1

    # ── 4. Validate migration structure ────────────────────────────────
    print()
    print("=" * 50)
    print("MIGRATION STRUCTURAL CHECKS")
    print("=" * 50)
    with open(
        "alembic/versions/a1b2c3d4e5f6_add_compliance_rules_full_schema.py",
        "r", encoding="utf-8",
    ) as fh:
        mig = fh.read()

    mig_checks = [
        ("Chains from baseline 9c6af0989667", "9c6af0989667" in mig),
        ("Creates uuid-ossp extension", "uuid-ossp" in mig),
        ("Creates btree_gin extension", "btree_gin" in mig),
        ("Creates risk_tier_enum type", "risk_tier_enum" in mig),
        ("Adds description column", "description" in mig),
        ("Adds annex_ref column", "annex_ref" in mig),
        ("Adds blocks_deployment column", "blocks_deployment" in mig),
        ("Adds requires_documentation column", "requires_documentation" in mig),
        ("Adds remediation_text column", "remediation_text" in mig),
        ("Adds updated_at column", "updated_at" in mig),
        ("Creates GIN index", "ix_compliance_rules_rule_tree" in mig),
        ("Has upgrade() function", "def upgrade" in mig),
        ("Has downgrade() function", "def downgrade" in mig),
    ]

    for name, passed in mig_checks:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
        if not passed:
            errors += 1

    # ── 5. Validate ORM model ──────────────────────────────────────────
    print()
    print("=" * 50)
    print("ORM MODEL CHECKS (database/models.py)")
    print("=" * 50)
    with open("database/models.py", "r", encoding="utf-8") as fh:
        model = fh.read()

    model_columns = [
        "rule_code", "title", "description", "risk_tier",
        "source_ref", "annex_ref", "rule_tree", "blocks_deployment",
        "requires_documentation", "remediation_text", "effective_date",
        "is_active", "created_at", "updated_at",
    ]
    for col in model_columns:
        present = col in model
        status = "PASS" if present else "FAIL"
        print(f"  [{status}] Column: {col}")
        if not present:
            errors += 1

    # ── Summary ────────────────────────────────────────────────────────
    print()
    print("=" * 50)
    if errors == 0:
        print("ALL CHECKS PASSED — Deliverables are ready.")
    else:
        print(f"FAILED: {errors} check(s) did not pass.")
    print("=" * 50)
    sys.exit(errors)


if __name__ == "__main__":
    main()
