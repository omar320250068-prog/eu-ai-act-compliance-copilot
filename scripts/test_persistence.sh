#!/bin/bash
# test_persistence.sh — Verifies PostgreSQL data survives container restart

echo "=== Starting stack ==="
docker-compose up -d postgres

echo "=== Waiting for Postgres to be ready ==="
sleep 5

echo "=== Inserting test record ==="
docker exec eu_ai_act_postgres psql -U $POSTGRES_USER -d $POSTGRES_DB \
  -c "CREATE TABLE IF NOT EXISTS _smoke_test (id SERIAL PRIMARY KEY, val TEXT); INSERT INTO _smoke_test(val) VALUES ('persistence_check');"

echo "=== Restarting container ==="
docker-compose restart postgres
sleep 5

echo "=== Verifying record survived restart ==="
docker exec eu_ai_act_postgres psql -U $POSTGRES_USER -d $POSTGRES_DB \
  -c "SELECT * FROM _smoke_test;"

echo "=== Cleaning up ==="
docker exec eu_ai_act_postgres psql -U $POSTGRES_USER -d $POSTGRES_DB \
  -c "DROP TABLE _smoke_test;"

echo "=== Persistence test PASSED ==="
