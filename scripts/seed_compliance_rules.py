# seed_compliance_rules.py
# ──────────────────────────────────────────────────────────────────────
# EU AI Act Compliance Co-Pilot — Rule Seeding Script
#
# Requirements: sqlalchemy[asyncio] asyncpg python-dotenv
# Usage:        DATABASE_URL=postgresql+asyncpg://... python seed_compliance_rules.py
# Safe to re-run: uses ON CONFLICT (rule_code) upsert logic
# ──────────────────────────────────────────────────────────────────────

# ─── SECTION B: Imports ──────────────────────────────────────────────
import asyncio
import logging
import os
import json
import uuid as _uuid
from pathlib import Path
from datetime import date

from dotenv import load_dotenv

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    Date,
    DateTime,
    Enum as PgEnum,
    Index,
    func,
    inspect,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.dialects.postgresql import insert as pg_insert

# ─── SECTION C: Logging Configuration ────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# ─── SECTION D: Effective Date Mapping ───────────────────────────────
# Legally mandated application dates per Regulation (EU) 2024/1689
TIER_EFFECTIVE_DATES = {
    "UNACCEPTABLE": date(2025, 2, 2),
    "HIGH":         date(2026, 8, 2),
    "LIMITED":      date(2026, 8, 2),
    "MINIMAL":      date(2026, 8, 2),
}


# ─── SECTION E: ORM Model ────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


class ComplianceRule(Base):
    """SQLAlchemy ORM model for the compliance_rules table.

    Mirrors Omar Hendawy's PostgreSQL schema column-for-column.
    """

    __tablename__ = "compliance_rules"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=_uuid.uuid4,
        server_default=func.uuid_generate_v4(),
    )
    rule_code = Column(String(20), unique=True, nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    risk_tier = Column(
        PgEnum(
            "UNACCEPTABLE", "HIGH", "LIMITED", "MINIMAL",
            name="risk_tier_enum",
            create_type=False,
        ),
        nullable=False,
    )
    source_ref = Column(String(200), nullable=True)
    annex_ref = Column(String(100), nullable=True)
    rule_tree = Column(JSONB, nullable=False)
    blocks_deployment = Column(Boolean, default=False)
    requires_documentation = Column(Boolean, default=False)
    remediation_text = Column(Text, nullable=True)
    effective_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        Index(
            "ix_compliance_rules_rule_tree",
            rule_tree,
            postgresql_using="gin",
        ),
    )


# ─── SECTION F: Engine & Session Factory ──────────────────────────────
load_dotenv()

try:
    DATABASE_URL = os.environ["DATABASE_URL"]
except KeyError:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. "
        "Expected format: postgresql+asyncpg://user:pass@host:port/dbname"
    )

engine = create_async_engine(DATABASE_URL, echo=False)
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ─── SECTION G: Async Seeding Function ───────────────────────────────
async def seed_rules() -> None:
    """Load compliance rules from JSON and upsert into PostgreSQL.

    Uses a single transaction with full rollback on failure.
    Idempotent: safe to run multiple times via ON CONFLICT upsert.
    """
    # Locate the JSON data file in the same directory as this script
    data_path = Path(__file__).resolve().parent / "compliance_rules_data.json"
    if not data_path.exists():
        logger.error("Data file not found: %s", data_path)
        raise FileNotFoundError(f"Required data file missing: {data_path}")

    with open(data_path, "r", encoding="utf-8") as f:
        rules = json.load(f)

    logger.info("Loaded %d rule(s) from %s", len(rules), data_path.name)

    inserted = 0
    updated = 0
    skipped = 0

    async with async_session_factory() as session:
        try:
            for rule in rules:
                # ── Validation: title must be non-null ──
                if not rule.get("title"):
                    logger.warning(
                        "Skipping rule %s — missing 'title' field",
                        rule.get("rule_id", "<unknown>"),
                    )
                    skipped += 1
                    continue

                tier = rule.get("risk_tier", "MINIMAL")
                effective = TIER_EFFECTIVE_DATES.get(tier)

                # Extract legal reference fields
                legal_ref = rule.get("legal_reference", {})
                source_ref = legal_ref.get("article", "")
                annex_ref = legal_ref.get("annex")

                # Build the values dict matching all table columns
                values = {
                    "rule_code": rule["rule_id"],
                    "title": rule["title"],
                    "description": rule.get("description", ""),
                    "risk_tier": tier,
                    "source_ref": source_ref,
                    "annex_ref": annex_ref,
                    "rule_tree": rule.get("rule_tree", {}),
                    "blocks_deployment": rule.get("blocks_deployment", False),
                    "requires_documentation": rule.get("requires_documentation", False),
                    "remediation_text": rule.get("remediation_text"),
                    "effective_date": effective,
                    "is_active": True,
                }

                # Build the ON CONFLICT DO UPDATE set (exclude PK and audit cols)
                update_cols = {
                    "title": values["title"],
                    "description": values["description"],
                    "risk_tier": values["risk_tier"],
                    "source_ref": values["source_ref"],
                    "annex_ref": values["annex_ref"],
                    "rule_tree": values["rule_tree"],
                    "blocks_deployment": values["blocks_deployment"],
                    "requires_documentation": values["requires_documentation"],
                    "remediation_text": values["remediation_text"],
                    "effective_date": values["effective_date"],
                    "is_active": True,
                    "updated_at": func.now(),
                }

                stmt = (
                    pg_insert(ComplianceRule)
                    .values(**values)
                    .on_conflict_do_update(
                        index_elements=["rule_code"],
                        set_=update_cols,
                    )
                    .returning(ComplianceRule.created_at, ComplianceRule.updated_at)
                )

                result = await session.execute(stmt)
                row = result.fetchone()

                # Determine if this was an INSERT (new) or UPDATE (existing)
                # by comparing created_at and updated_at timestamps
                if row and row[0] == row[1]:
                    inserted += 1
                else:
                    updated += 1

            await session.commit()
            logger.info("─── Seeding Complete ───")
            logger.info("  %d rules inserted (new)", inserted)
            logger.info("  %d rules updated (existing)", updated)
            logger.info("  %d rules skipped (validation failure)", skipped)
            logger.info("  %d total rules processed", inserted + updated + skipped)

        except Exception:
            await session.rollback()
            logger.error("Transaction rolled back due to error", exc_info=True)
            raise

    await engine.dispose()
    logger.info("Database engine disposed. Seeding script finished.")


# ─── SECTION H: Entry Point ──────────────────────────────────────────
if __name__ == "__main__":
    asyncio.run(seed_rules())
