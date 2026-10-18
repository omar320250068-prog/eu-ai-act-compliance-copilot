"""
test_pipeline.py
Automated validation of the Omar Hendawy Database Architecture Tasks.
"""
import os
import asyncio
import asyncpg
import json
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL", "").replace("+asyncpg", "").replace("postgres:5433", "127.0.0.1:5433")

async def run_tests():
    print("=== STARTING ARCHITECTURE VALIDATION TESTS ===")

    # -------------------------------------------------------------
    # TEST 1: Boot Database
    # -------------------------------------------------------------
    print("\n[TEST 1: Boot Database]")
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        version = await conn.fetchval("SELECT version();")
        print("✅ SUCCESS: Connected to PostgreSQL! Server Version:")
        print(f"   {version.split(' (')[0]}")
    except Exception as e:
        print(f"❌ FAILED: Could not connect to database. {e}")
        return

    # -------------------------------------------------------------
    # TEST 2: Schema Creation (Alembic Migrations)
    # -------------------------------------------------------------
    print("\n[TEST 2: Schema Creation (Tables & Enums)]")
    try:
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        table_names = [record['table_name'] for record in tables]
        
        expected_tables = ["projects", "assessments", "compliance_rules", "alembic_version"]
        missing_tables = [t for t in expected_tables if t not in table_names]
        
        if not missing_tables:
            print("✅ SUCCESS: All required schemas and Alembic versioning tables exist!")
            print(f"   Detected tables: {table_names}")
        else:
            print(f"❌ FAILED: Missing schemas: {missing_tables}")
    except Exception as e:
        print(f"❌ FAILED: Query error. {e}")

    # -------------------------------------------------------------
    # TEST 3: Seed the Data
    # -------------------------------------------------------------
    print("\n[TEST 3: Seed The Specific Legal Data (JSONB Check)]")
    try:
        rule_row = await conn.fetchrow("""
            SELECT rule_code, risk_tier, rule_tree 
            FROM compliance_rules 
            WHERE rule_code = 'ART_5_1_A';
        """)
        if rule_row:
            tree_data = json.loads(rule_row['rule_tree'])
            print("✅ SUCCESS: Seed data found!")
            print(f"   Rule Code: {rule_row['rule_code']}")
            print(f"   Risk Tier: {rule_row['risk_tier']}")
            print(f"   Nested JSON Outcomes: {tree_data.get('outcome')}")
        else:
            print("❌ FAILED: Rule 'ART_5_1_A' is completely missing from database.")
    except Exception as e:
        print(f"❌ FAILED: Query error on seed data. {e}")

    await conn.close()
    print("\n=== ALL TESTS COMPLETED ===")

if __name__ == "__main__":
    asyncio.run(run_tests())
