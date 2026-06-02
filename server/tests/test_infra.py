# Run against SQLite (default, no setup required):
#   pytest server/tests/test_infra.py
#
# Run against PostgreSQL (requires a running Postgres instance):
#   DATABASE_URL=postgresql+psycopg2://user:pass@localhost/porquilo_test \
#     pytest server/tests/test_infra.py
#
# No dialect-specific syntax — the suite runs unmodified against both databases.

import datetime
import uuid

import sqlalchemy as sa


def test_write_and_read(db_session):
    mid = str(uuid.uuid4())
    db_session.execute(
        sa.text(
            "INSERT INTO meals (id, name, sort_order, is_default, created_at) "
            "VALUES (:id, :name, :sort_order, :is_default, :created_at)"
        ),
        {
            "id": mid,
            "name": "__infra_test__",
            "sort_order": 999,
            "is_default": False,
            "created_at": datetime.datetime.now(datetime.timezone.utc),
        },
    )
    db_session.flush()
    row = db_session.execute(
        sa.text("SELECT name FROM meals WHERE id = :id"), {"id": mid}
    ).fetchone()
    assert row is not None
    assert row[0] == "__infra_test__"


def test_clean_state(db_session):
    """Row inserted in test_write_and_read must not survive into this test."""
    count = db_session.execute(
        sa.text("SELECT COUNT(*) FROM meals WHERE name = '__infra_test__'")
    ).scalar()
    assert count == 0


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
