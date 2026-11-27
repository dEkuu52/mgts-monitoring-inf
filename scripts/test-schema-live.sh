#!/usr/bin/env bash
# Disposable, uniquely named databases in the isolated LOCAL preview only.
set -euo pipefail
cd "$(dirname "$0")/.."
compose=(docker compose -p mgts-preview -f compose.preview.yml)
suffix="$(date +%s)_$$"
fresh="mgts_fresh_$suffix"
legacy="mgts_legacy_$suffix"
for db in "$fresh" "$legacy"; do
  "${compose[@]}" exec -T db createdb -U preview "$db"
done

# Exact pre-cutover base schema; never drop tables or records in this fixture.
git show 05a644fbbdef1c2c19b9d8393c9aff88b5018b5c:migrations.sql |
  "${compose[@]}" exec -T db psql -U preview -d "$legacy" -v ON_ERROR_STOP=1
"${compose[@]}" exec -T db psql -U preview -d "$legacy" -v ON_ERROR_STOP=1 -c "
  CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL PRIMARY KEY);
  INSERT INTO alembic_version VALUES ('20261124_0001');
  INSERT INTO users(email, username) VALUES ('schema@example.invalid', 'preserve_user');
  INSERT INTO statuses(type, description) VALUES ('legacy_keep', 'preserve status');
  INSERT INTO infrastructure_objects(type, place) VALUES ('legacy_keep', 'preserve object');
"

for db in "$fresh" "$legacy"; do
  # Exercise the exact Compose psql initializer twice. It uses -1 and must be repeatable.
  "${compose[@]}" run --rm --no-deps -e PGDATABASE="$db" schema-init
  "${compose[@]}" run --rm --no-deps -e PGDATABASE="$db" schema-init
  tables=$("${compose[@]}" exec -T db psql -U preview -d "$db" -Atc \
    "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('users','statuses','infrastructure_objects','defects')")
  [[ "$tables" == 4 ]]
  added_columns=$("${compose[@]}" exec -T db psql -U preview -d "$db" -Atc "
    SELECT count(*) FROM information_schema.columns WHERE table_schema='public' AND
      (table_name='users' AND column_name='password_hash' OR
       table_name='infrastructure_objects' AND column_name IN ('external_id','lat','lon','processing_status','processing_started_at','processing_attempts','processing_error','processed_at','processed_img_url') OR
       table_name='defects' AND column_name IN ('bbox','source'))")
  [[ "$added_columns" == 12 ]]
  unrecognized=$("${compose[@]}" exec -T db psql -U preview -d "$db" -Atc \
    "SELECT count(*) FROM statuses WHERE type='unrecognized'")
  [[ "$unrecognized" == 1 ]]
done

fresh_version_table=$("${compose[@]}" exec -T db psql -U preview -d "$fresh" -Atc \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_name='alembic_version'")
[[ "$fresh_version_table" == 0 ]]
legacy_version=$("${compose[@]}" exec -T db psql -U preview -d "$legacy" -Atc \
  'SELECT version_num FROM alembic_version')
[[ "$legacy_version" == 20261124_0001 ]]
preserved=$("${compose[@]}" exec -T db psql -U preview -d "$legacy" -Atc "
  SELECT (SELECT count(*) FROM users WHERE username='preserve_user') +
         (SELECT count(*) FROM statuses WHERE type='legacy_keep') +
         (SELECT count(*) FROM infrastructure_objects WHERE place='preserve object')")
[[ "$preserved" == 3 ]]
printf 'PASS fresh + repeat + legacy schema/data preservation; old version row untouched. Test databases retained: %s %s\n' "$fresh" "$legacy"
