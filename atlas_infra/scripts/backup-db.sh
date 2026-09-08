#!/usr/bin/env bash
# Backup do PostgreSQL do Atlas Vivo MILK.
# Uso: ./scripts/backup-db.sh  (gera atlas_vivo_YYYYMMDD.sql.gz)
set -euo pipefail
cd "$(dirname "$0")/.."

TS=$(date +%Y%m%d_%H%M%S)
OUT="backups/atlas_vivo_${TS}.sql.gz"
mkdir -p backups

docker compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U "${POSTGRES_USER:-milk}" -d "${POSTGRES_DB:-atlas_vivo}" \
  | gzip > "$OUT"

echo "Backup criado: $OUT  ($(du -h "$OUT" | cut -f1))"
