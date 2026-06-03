# Porquilo — Server

FastAPI nutrition tracker. SQLite in dev, PostgreSQL in prod. Single-user for now.

---

## Non-negotiables

- **Never call `SQLModel.metadata.create_all()` or `drop_all()`** — Alembic is the source of truth. Read the migration files to confirm column names, types, and nullability before writing or modifying models. Do not infer from memory.
- **Dialect-neutral SQL only** — no SQLite or PostgreSQL specific syntax anywhere in app or test code.
- **`DATABASE_URL`** controls the connection string. Fallback: `sqlite:///./porquilo.db` in app code, `sqlite:///:memory:` in tests.
- **All queries go through a SQLModel session** — no raw SQL.

---

## Primary keys

UUID on every table. Use `sa_column=sa.Column(sa.Uuid)` in SQLModel field definitions — not Python's `uuid.UUID` type annotation alone. Request and response Pydantic models use `UUID` types, not `int`.

---

## Open strings

Fields like `weight_source`, `weight_confidence`, `input_method`, `sync_status`, `metric_type`, and `source` are open/extensible strings. Use plain `str` in SQLModel models and Pydantic schemas — no Python `Enum` types.

---

## Project structure

```
server/
  src/porquilo/
    main.py              ← FastAPI app instance
    core/
      database.py        ← get_session() dependency
    models/              ← One SQLModel class per table, all exported from __init__.py
    routers/             ← One file per route group (foods.py, log.py, diary.py)
    services/            ← Shared business logic (nutrients.py)
  alembic/
    versions/            ← Migration files — source of truth, never modify
  tests/
    conftest.py          ← Shared fixtures (engine, db_session, override_get_session, client)
```

---

## Key schema decisions

### `source` fields on `foods`

The `foods` table does not have a `source` string column. It has:

- `food_source_id` — UUID FK → `food_sources.id`
- `external_source_id` — text, nullable (the food's identifier in the external system)

API-facing Pydantic models use friendlier names for readability. Routes must translate:

| API field | DB column | How |
|-----------|-----------|-----|
| `source` (string key, e.g. `'usda'`) | `food_source_id` (UUID) | Look up `food_sources` by `key`, use the UUID |
| `source_id` | `external_source_id` | Store directly |
| `source` in responses | `food_sources.key` | Join `food_sources`, return `key` |

### `ingredients` abstraction layer

`log_entries` stores `ingredient_id` (FK → `ingredients`), not `food_id` directly. The `ingredients` table lets foods and recipes appear uniformly in log entries and recipe contents.

For Phase 1 (foods only), any route that creates a log entry must resolve `food_id → ingredient_id`:

1. `SELECT id FROM ingredients WHERE food_id = :food_id`
2. If no row exists, insert one (`food_id` set, `recipe_id` null)
3. Use the resulting `ingredient_id` on the `LogEntry`

Diary queries that need `food_name` must join through the same abstraction:
`log_entries → ingredients → foods` (`LogEntry.ingredient_id → Ingredient.food_id → Food.name`)

### Timestamps

Naive UTC datetimes throughout — no timezone-aware types. Two distinct columns on `log_entries`:

- `eaten_at` — when the food was consumed. User-provided. Shown in the UI.
- `logged_at` — when the row was created. Set server-side to `datetime.utcnow()`. Never accepted from the client. Audit only.

Do not use database-native `date()` or timezone conversion functions — they are not dialect-neutral and SQLite's behavior with UTC datetimes is unreliable. For date-based filtering, use a range query in Python:

```python
day_start = datetime(year, month, day)
day_end = day_start + timedelta(days=1)
# WHERE eaten_at >= day_start AND eaten_at < day_end
```

---

## Tests

- Fixtures live in `server/tests/conftest.py`
- The suite runs against both SQLite and PostgreSQL by switching `DATABASE_URL` — no other changes required
- No globally seeded test data — each test creates what it needs
- Migrations run once per test run via `alembic.command.upgrade`; each test rolls back via savepoint