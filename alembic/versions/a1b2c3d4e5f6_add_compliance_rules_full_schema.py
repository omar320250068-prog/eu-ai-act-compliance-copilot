"""add_compliance_rules_full_schema

Revision ID: a1b2c3d4e5f6
Revises: 9c6af0989667
Create Date: 2026-04-22 22:00:00.000000

This migration upgrades the compliance_rules table to the full schema
required by Ismail's seeding script, adds the risk_tier_enum PostgreSQL
type, enables required extensions, and creates a GIN index on rule_tree.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "9c6af0989667"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Enable required PostgreSQL extensions ──────────────────────
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "btree_gin"')

    # ── 2. Create the risk_tier_enum type ─────────────────────────────
    # The baseline migration used an inline Enum named 'risktier'.
    # We create the canonical 'risk_tier_enum' type for the new columns.
    op.execute(
        "DO $$ BEGIN "
        "  CREATE TYPE risk_tier_enum AS ENUM "
        "    ('UNACCEPTABLE','HIGH','LIMITED','MINIMAL'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; "
        "END $$"
    )

    # ── 3. Add missing columns to compliance_rules ────────────────────
    op.add_column(
        "compliance_rules",
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.add_column(
        "compliance_rules",
        sa.Column("annex_ref", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "compliance_rules",
        sa.Column("blocks_deployment", sa.Boolean(), server_default="false"),
    )
    op.add_column(
        "compliance_rules",
        sa.Column("requires_documentation", sa.Boolean(), server_default="false"),
    )
    op.add_column(
        "compliance_rules",
        sa.Column("remediation_text", sa.Text(), nullable=True),
    )
    op.add_column(
        "compliance_rules",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )

    # ── 4. Alter rule_code from VARCHAR(50) → VARCHAR(20) ────────────
    op.alter_column(
        "compliance_rules",
        "rule_code",
        type_=sa.String(length=20),
        existing_type=sa.String(length=50),
        existing_nullable=False,
    )

    # ── 5. Alter risk_tier to use the new risk_tier_enum type ─────────
    # Cast existing data from the old 'risktier' enum to the new type
    op.execute(
        "ALTER TABLE compliance_rules "
        "ALTER COLUMN risk_tier TYPE risk_tier_enum "
        "USING risk_tier::text::risk_tier_enum"
    )

    # ── 6. Create GIN index on rule_tree JSONB column ─────────────────
    # NOTE: CREATE INDEX CONCURRENTLY cannot run inside a transaction.
    # Alembic runs migrations inside a transaction by default.
    # We use a non-concurrent index here for transactional safety.
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_compliance_rules_rule_tree "
        "ON compliance_rules USING GIN (rule_tree)"
    )


def downgrade() -> None:
    # ── Drop the GIN index ────────────────────────────────────────────
    op.execute("DROP INDEX IF EXISTS ix_compliance_rules_rule_tree")

    # ── Revert risk_tier back to original risktier enum ───────────────
    op.execute(
        "ALTER TABLE compliance_rules "
        "ALTER COLUMN risk_tier TYPE risktier "
        "USING risk_tier::text::risktier"
    )

    # ── Revert rule_code length ───────────────────────────────────────
    op.alter_column(
        "compliance_rules",
        "rule_code",
        type_=sa.String(length=50),
        existing_type=sa.String(length=20),
        existing_nullable=False,
    )

    # ── Drop added columns (reverse order of addition) ────────────────
    op.drop_column("compliance_rules", "updated_at")
    op.drop_column("compliance_rules", "remediation_text")
    op.drop_column("compliance_rules", "requires_documentation")
    op.drop_column("compliance_rules", "blocks_deployment")
    op.drop_column("compliance_rules", "annex_ref")
    op.drop_column("compliance_rules", "description")

    # ── Drop the new enum type ────────────────────────────────────────
    op.execute("DROP TYPE IF EXISTS risk_tier_enum")

    # NOTE: Extensions (uuid-ossp, btree_gin) are NOT dropped in
    # downgrade — they may be used by other tables in the deployment.
