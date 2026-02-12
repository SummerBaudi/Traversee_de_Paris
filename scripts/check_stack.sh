#!/usr/bin/env bash
set -euo pipefail

echo "[1/3] Validate docker-compose syntax"
docker compose config >/dev/null

echo "[2/3] Run geo pipeline placeholder"
python3 services/geo-pipeline/run_pipeline.py >/dev/null

echo "[3/3] Check report exists"
test -f artifacts/reports/geo_pipeline_report.json

echo "All checks passed"
