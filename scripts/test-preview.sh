#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
bash -n scripts/preview.sh
if scripts/preview.sh invalid >/dev/null 2>&1; then exit 1; fi
docker compose -p mgts-preview -f compose.preview.yml config --format json | uv run python -c '
import json,sys
c=json.load(sys.stdin); s=c["services"]
assert set(s)=={"db","schema-init","minio","backend","frontend"}
assert not s["db"].get("ports") and not s["minio"].get("ports")
assert s["frontend"]["ports"][0]["host_ip"]=="127.0.0.1"
assert s["backend"]["environment"]["S3_ENDPOINT"]=="http://minio:9000"
schema=s["schema-init"]
assert schema["image"] == "postgres:15-alpine"
assert schema["command"] == ["psql", "-v", "ON_ERROR_STOP=1", "-1", "-f", "/schema/schema.sql"]
assert schema["depends_on"]["db"]["condition"] == "service_healthy"
assert schema["volumes"][0]["target"] == "/schema/schema.sql"
assert s["backend"]["depends_on"]["schema-init"]["condition"] == "service_completed_successfully"
assert all("container_name" not in v for v in s.values())
print("preview configuration: PASS")'
MGTS_DB_PASSWORD=test-db MGTS_STORAGE_PASSWORD=test-storage MGTS_JWT_SECRET=test-jwt MGTS_PREVIEW_PASSWORD_HASH=test-hash MGTS_PREVIEW_HOST=preview.invalid docker compose -p mgts-static -f compose.dokploy.yml config --format json | uv run python -c '
import json,sys
c=json.load(sys.stdin); s=c["services"]
assert s["schema-init"]["image"] == "postgres:15-alpine"
assert s["schema-init"]["environment"]["PGPASSWORD"] == "test-db"
assert s["backend"]["depends_on"]["schema-init"]["condition"] == "service_completed_successfully"
assert s["gateway"]["labels"]["mgts.gateway-config"] == "admin-login-v1"
content=c["configs"]["gateway"]["content"]
assert "admin " in content and "preview " not in content
print("Dokploy Compose config: PASS")'
uv run python - <<'CHECK'
from pathlib import Path
assert not Path('scripts/preview-schema.sql').exists()
assert not Path('migrations.sql').exists()
assert Path('backend/sql/schema.sql').is_file()
assert not Path('backend/alembic.ini').exists()
assert not Path('backend/migrations').exists()
assert 'alembic' not in Path('backend/requirements.txt').read_text().lower()
assert 'alembic' not in Path('backend/Dockerfile').read_text().lower()
assert 'alembic' not in Path('backend/worker.Dockerfile').read_text().lower()
for compose_file in ('docker-compose.yml', 'compose.preview.yml', 'compose.dokploy.yml'):
    assert 'alembic' not in Path(compose_file).read_text().lower()
print('backend SQL schema ownership: PASS')
CHECK
