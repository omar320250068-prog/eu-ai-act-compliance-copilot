# EU AI Act Compliance Co-Pilot — Data Layer

> **Compliance-as-code for the EU AI Act.** An MVP that classifies AI systems into the four regulatory **risk tiers** of Regulation (EU) 2024/1689 — so teams can catch high-risk systems *before* they ship.

![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00)
![Alembic](https://img.shields.io/badge/Alembic-migrations-6BA81E)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-compose-2496ED?logo=docker&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## Why

The EU AI Act is the first comprehensive legal framework for artificial intelligence. Non-compliance is expensive — penalties scale up to **€35 million or 7% of global annual turnover**, whichever is higher.

Most teams do not fail because they *ignore* the law; they fail because they cannot translate a dense legal text into an engineering decision. This project closes that gap: it turns the Act into a **queryable rule registry** and a **deterministic assessment pipeline** that maps a plain-language system description onto one of four tiers.

| Tier | Meaning | Consequence |
|------|---------|-------------|
| `UNACCEPTABLE` | Prohibited practices (Art. 5) | Cannot be deployed in the EU |
| `HIGH` | High-risk systems (Annex III) | Heavy obligations: documentation, conformity assessment, human oversight |
| `LIMITED` | Transparency obligations (Art. 50) | Disclosure duties |
| `MINIMAL` | Everything else | No additional obligations |

## What this repository is

This is the **data & compliance layer** of the MVP — the relational backbone that

1. stores every submitted AI project,
2. stores the AI model's risk classification alongside its full inference payload (for audit and drift analysis),
3. stores the **EU AI Act rules themselves** as structured, machine-evaluable `JSONB` rule trees, and
4. exposes an async FastAPI surface so the frontend and the AI model can read and write through one contract.

> It was built as a cross-functional academic MVP; this repo focuses on the database architecture, migrations, legal-rule seeding, and backend integration. See [Contributors](#contributors) for the full team.

## Architecture

```mermaid
graph TD
    UI["Frontend (React)"] -->|POST /api/assess| API["FastAPI Backend"]
    API -->|validate| Pydantic["Pydantic DTOs"]
    Pydantic --> AI["Risk-classification model"]
    AI --> API
    API -->|async write| DB[("PostgreSQL 16")]
    Seed["Seed script<br/>(legal rule trees)"] -->|upsert| DB
    DB -->|GIN / JSONB query| API
    API -->|report JSON| UI

    subgraph "This repository"
        API
        Pydantic
        DB
        Seed
    end
```

## Tech stack

| Layer | Choice |
|-------|--------|
| Database | PostgreSQL 16 (`uuid-ossp`, `btree_gin`, native `JSONB`) |
| ORM | SQLAlchemy 2.0 (async, `asyncpg` driver) |
| Migrations | Alembic |
| API | FastAPI + Uvicorn |
| Validation | Pydantic v2 |
| Packaging | Docker / Docker Compose |
| Backup | `pg_dump` script (`scripts/backup.sh`) |

## Repository structure

```
.
├── alembic/                     # Migration pipeline
│   ├── versions/
│   │   ├── 9c6af0989667_baseline_schema.py
│   │   └── a1b2c3d4e5f6_add_compliance_rules_full_schema.py
│   └── env.py
├── backend/
│   ├── main.py                  # FastAPI app (/api/assess, /api/rules)
│   └── requirements.txt
├── database/
│   ├── engine.py                # Async engine + session factory
│   └── models.py                # ORM models (shared contract)
├── sql/                         # Canonical raw schema
│   ├── 001_create_projects.sql
│   ├── 002_create_assessments.sql
│   ├── 003_create_compliance_rules.sql
│   └── 004_create_indexes.sql
├── scripts/
│   ├── seed_compliance_rules.py     # Idempotent upsert seeder
│   ├── compliance_rules_data.json   # Structured EU AI Act rules
│   ├── validate_deliverables.py     # Schema/ORM/migration checks
│   ├── backup.sh                    # Automated pg_dump
│   └── test_*.{py,sh}               # Pipeline & persistence tests
├── docker-compose.yml           # Postgres + backend
├── Dockerfile
├── requirements.txt
├── FULL_PROJECT_PLAN.md         # Original MVP master plan
└── .env.example
```

## Data model

Three normalized tables, joined by `project_id`:

**`projects`** — inputs. User-submitted AI system descriptions.
`id` (UUID PK) · `name` · `description` · `submitter_email` · `deployment_context` · `created_at` / `updated_at` (auto-updated by trigger).

**`assessments`** — outputs. One row per model classification.
`id` (UUID PK) · `project_id` (FK, `ON DELETE CASCADE`) · `risk_tier` (enum) · `confidence_score` (`NUMERIC(5,4)`, constrained `0–1`) · `reasoning` · `raw_model_output` (`JSONB`, retained for audit & model-drift analysis) · `model_version` · `assessed_at`.

**`compliance_rules`** — the law, as data.
`id` (UUID PK) · `rule_code` (unique, e.g. `ART_6_1`) · `title` · `description` · `risk_tier` (enum) · `source_ref` · `annex_ref` · `rule_tree` (**`JSONB`** — nested, machine-evaluable conditions) · `blocks_deployment` · `requires_documentation` · `remediation_text` · `effective_date` · `is_active`.

A `rule_tree` looks like:

```json
{
  "conditions": [
    {
      "field": "deployment_context",
      "operator": "in",
      "values": ["biometric_identification", "law_enforcement"],
      "sub_conditions": [
        { "field": "real_time", "operator": "equals", "values": [true] }
      ]
    }
  ],
  "outcome": "UNACCEPTABLE",
  "legal_basis": "Article 5(1)(a)"
}
```

### Indexing strategy

Indexes are written **for the access patterns that actually exist**, not speculatively — see `sql/004_create_indexes.sql`:

- `assessments(project_id)` — the most common join.
- `assessments(project_id, risk_tier)` — composite for "all HIGH-risk assessments of a project".
- `projects(created_at DESC)` — time-series dashboards.
- `compliance_rules(is_active) WHERE is_active = TRUE` — **partial index**; nearly every evaluation query filters on it.
- `compliance_rules USING GIN (rule_tree)` — enables `@>`, `?`, `?|`, `?&` containment operators against the JSONB rule trees.

## Getting started

### Option A — Docker (recommended)

```bash
cp .env.example .env          # then set real values
docker compose up --build     # starts Postgres (:5433) + backend (:8000)
```

### Option B — Local

```bash
python -m venv .venv
. .venv/Scripts/activate       # Windows:  .venv\Scripts\activate
pip install -r requirements.txt -r backend/requirements.txt
```

Set `DATABASE_URL`, then apply the schema and seed the rules:

```bash
alembic upgrade head
python scripts/seed_compliance_rules.py
uvicorn backend.main:app --reload
```

### Environment variables

| Variable | Purpose |
|----------|---------|
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | Postgres credentials |
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@host:5432/dbname` |

See `.env.example`. **Never commit real `.env` files** — they are git-ignored.

## Migrations

The pipeline is linear and reversible:

```
9c6af0989667  baseline schema (projects, assessments, compliance_rules)
      │
a1b2c3d4e5f6  compliance_rules full schema
              (uuid-ossp + btree_gin, risk_tier_enum,
               description, annex_ref, blocks_deployment,
               requires_documentation, remediation_text,
               updated_at, GIN index on rule_tree)
```

```bash
alembic upgrade head          # apply
alembic downgrade -1          # roll back one revision
```

## Seeding the legal rules

`scripts/seed_compliance_rules.py` loads `scripts/compliance_rules_data.json` and **upserts** every rule with `ON CONFLICT (rule_code) DO UPDATE` inside a single transaction (full rollback on failure). It is **idempotent** — safe to run repeatedly — and assigns legally mandated effective dates per tier:

| Tier | Applies from |
|------|--------------|
| `UNACCEPTABLE` | 2025-02-02 |
| `HIGH` / `LIMITED` / `MINIMAL` | 2026-08-02 |

Validate everything at once:

```bash
python scripts/validate_deliverables.py
```

## API

| Method | Route | Description |
|--------|-------|-------------|
| `POST` | `/api/assess` | Store a project + its risk assessment in one flow |
| `GET`  | `/api/rules?tier=HIGH` | Fetch active compliance rules, optionally filtered by tier |

## Backup

```bash
bash scripts/backup.sh        # timestamped, gzip-compressed pg_dump
```

Designed to be scheduled as a daily cron / Task Scheduler job.

## Testing

```bash
pytest                                   # local
./test_with_docker.ps1                   # end-to-end against the compose stack
python test_backend.py                   # backend pipeline smoke test
```

## Contributors

Built as a cross-functional MVP. Roles from the original master plan:

- **Omar Hindawy** — Database architecture, schema design, migrations, indexing, backups *(this repository)*
- Ahmed El-Desouky — Backend & AI integration
- Ahmed Hossam — Frontend
- Mohamed Ismail — Compliance research & rule structuring
- Moaz El-Garwany — NLP model training
- Youssef Kamal — Hardware & infrastructure

## License

[MIT](LICENSE) © 2026 Omar Hindawy
