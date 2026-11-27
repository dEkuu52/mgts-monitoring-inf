from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]


def normalize_sql(sql: str) -> str:
    return " ".join(sql.split())


# Every statement in the previously delivered initial revision, retained in
# order so the SQL initializer cannot silently lose part of its schema.
EXPECTED_STATEMENTS = tuple(
    map(
        normalize_sql,
        (
            """CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) NOT NULL UNIQUE,
                phone VARCHAR(50),
                username VARCHAR(100) NOT NULL UNIQUE,
                role VARCHAR(50) NOT NULL DEFAULT 'user',
                update_at TIMESTAMP NOT NULL DEFAULT NOW(),
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            )""",
            """CREATE TABLE IF NOT EXISTS statuses (
                id SERIAL PRIMARY KEY,
                type VARCHAR(100) NOT NULL,
                description TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS infrastructure_objects (
                id SERIAL PRIMARY KEY,
                "imgUrl" TEXT,
                type VARCHAR(100),
                "statusId" INTEGER REFERENCES statuses(id) ON DELETE SET NULL,
                place TEXT
            )""",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255)",
            "ALTER TABLE infrastructure_objects ADD COLUMN IF NOT EXISTS external_id VARCHAR(100)",
            "ALTER TABLE infrastructure_objects ADD COLUMN IF NOT EXISTS lat DOUBLE PRECISION",
            "ALTER TABLE infrastructure_objects ADD COLUMN IF NOT EXISTS lon DOUBLE PRECISION",
            "ALTER TABLE infrastructure_objects ADD COLUMN IF NOT EXISTS processing_status VARCHAR(32)",
            "ALTER TABLE infrastructure_objects ADD COLUMN IF NOT EXISTS processing_started_at TIMESTAMP",
            "ALTER TABLE infrastructure_objects ADD COLUMN IF NOT EXISTS processing_attempts INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE infrastructure_objects ADD COLUMN IF NOT EXISTS processing_error TEXT",
            "ALTER TABLE infrastructure_objects ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP",
            "ALTER TABLE infrastructure_objects ADD COLUMN IF NOT EXISTS processed_img_url TEXT",
            """CREATE INDEX IF NOT EXISTS infrastructure_objects_processing_status_idx
                ON infrastructure_objects (processing_status)""",
            """CREATE TABLE IF NOT EXISTS defects (
                id SERIAL PRIMARY KEY,
                object_id INTEGER REFERENCES infrastructure_objects(id) ON DELETE SET NULL,
                detection_id INTEGER,
                defect_type VARCHAR(100) NOT NULL,
                defect_confidence DOUBLE PRECISION,
                severity VARCHAR(50),
                recommended_action VARCHAR(50),
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW()
            )""",
            "ALTER TABLE defects ADD COLUMN IF NOT EXISTS bbox JSONB",
            "ALTER TABLE defects ADD COLUMN IF NOT EXISTS source VARCHAR(20) NOT NULL DEFAULT 'manual'",
            "CREATE INDEX IF NOT EXISTS defects_object_id_idx ON defects (object_id)",
            'CREATE INDEX IF NOT EXISTS infrastructure_objects_status_id_idx ON infrastructure_objects ("statusId")',
            """INSERT INTO statuses (type, description)
                SELECT 'unrecognized', 'Не распознано'
                WHERE NOT EXISTS (SELECT 1 FROM statuses WHERE type = 'unrecognized')""",
        ),
    )
)


class SchemaOwnershipTests(unittest.TestCase):
    def test_schema_preserves_all_initial_revision_statements(self) -> None:
        schema = (BACKEND / "sql" / "schema.sql").read_text(encoding="utf-8")
        schema = re.sub(r"(?m)^\s*--.*$", "", schema)
        actual_statements = tuple(
            normalize_sql(statement)
            for statement in schema.split(";")
            if statement.strip()
        )
        self.assertEqual(actual_statements, EXPECTED_STATEMENTS)

    def test_schema_is_repeatable_and_has_no_destructive_ddl(self) -> None:
        schema = (BACKEND / "sql" / "schema.sql").read_text(encoding="utf-8")
        self.assertNotRegex(schema, r"(?im)^\s*(?:DROP|TRUNCATE)\b|^\s*DELETE\s+FROM\b")
        self.assertNotRegex(schema, r"(?i)\bCREATE\s+TABLE\s+(?!IF\s+NOT\s+EXISTS)")
        self.assertNotRegex(schema, r"(?i)\bCREATE\s+INDEX\s+(?!IF\s+NOT\s+EXISTS)")
        self.assertNotRegex(schema, r"(?i)\bADD\s+COLUMN\s+(?!IF\s+NOT\s+EXISTS)")
        self.assertIn("WHERE NOT EXISTS", schema)

    def test_no_alembic_runtime_or_dependency_remains(self) -> None:
        requirements = (BACKEND / "requirements.txt").read_text(encoding="utf-8")
        self.assertNotRegex(requirements, r"(?im)^\s*alembic\s*=")
        self.assertFalse((BACKEND / "alembic.ini").exists())
        self.assertFalse((BACKEND / "migrations").exists())

    def test_api_worker_and_seed_do_not_apply_schema_ddl(self) -> None:
        for relative_path in ("app/main.py", "worker.py", "seed.py"):
            with self.subTest(component=relative_path):
                tree = ast.parse((BACKEND / relative_path).read_text(encoding="utf-8"))
                names = {
                    node.id
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Name)
                }
                self.assertNotIn("bootstrap_schema", names)
                self.assertNotIn("create_all", names)
                self.assertNotIn("stamp", names)


if __name__ == "__main__":
    unittest.main()
