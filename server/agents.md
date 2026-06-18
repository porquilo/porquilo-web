# Porquilo — Server

FastAPI nutrition tracker. SQLite in dev, PostgreSQL in prod. Household-scale multi-user
with real per-user accounts — see `porquilo-mobile-app-decisions.md` §2–§4 for rationale.

---

## Package management

Use `uv` for all Python tooling — `uv run`, `uv add`, `uv sync`, etc. Do not use `pip` or `python` directly.

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
    main.py              ← FastAPI app instance + exception handler registration
    core/
      database.py        ← get_session() dependency
      deps.py            ← get_current_user, require_admin FastAPI dependencies
      errors.py          ← PorquiloError class + all error code constants
    models/              ← One SQLModel class per table, all exported from __init__.py
    routers/             ← One file per route group (foods.py, log.py, diary.py)
      auth.py            ← POST /api/auth/token, /logout, /password, /pairing/exchange
      users.py           ← Admin user management + pairing-code generation
    services/            ← Shared business logic (nutrients.py)
  alembic/
    versions/            ← Migration files — source of truth, never modify
  tests/
    conftest.py          ← Shared fixtures (engine, db_session, override_get_session, client)
```

---

## Users & auth

- `users` table: `id` (UUID PK), `username` (unique), `hashed_password`, `role`
  (`'admin'` | `'member'`), `display_name`, `units`, `timezone`. The planned Phase 1
  Profile stub (name, units preference, timezone) is folded into this table — do not
  build a separate profile table.
- Passwords hashed with **argon2 or bcrypt** (not yet decided — use `passlib`; never a
  homegrown scheme).
- Auth tokens are **opaque bearer tokens** stored server-side (not JWTs). The server
  looks up the token on every request. Tokens are long-lived but revocable.
- `POST /api/auth/token` accepts `username` + `password`, returns a token string.
- Every protected route uses a `get_current_user` FastAPI dependency injected via
  `Depends(get_current_user)` from `core/deps.py`. Never query user-scoped resources
  without it.
- Admin-only endpoints use `Depends(require_admin)`, which calls `get_current_user`
  first and then checks `role == 'admin'`.
- Bootstrap: the first account is created on first boot. Mechanism not yet decided —
  env-var read on first boot vs. interactive setup wizard on first dashboard visit.
  An empty `users` table is the signal to trigger whichever path is chosen.

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

### user_id ownership

`log_entries` and `body_metrics` each have a `user_id` FK → `users.id`. All queries
on these tables must filter by `current_user.id` — never return rows across users in
the same response. `goals` will get a `user_id` FK when that table is created in
Phase 4 — not before.

`foods`, `recipes`, and `meals` have no `user_id` — they are global to the instance.
A custom food, an imported Mealie recipe, or a configured meal slot is visible to all
users on the server by design.

---

### Direct FK approach for log entries and recipe ingredients

`log_entries` has `food_id` (FK → `foods.id`) and `recipe_id` (FK → `recipes.id`), both nullable. Exactly one must be set (enforced by `ck_log_entries_exactly_one_fk`). Routes that create a log entry set `food_id` directly for food entries and `recipe_id` directly for recipe entries.

`recipe_ingredients` has `food_id` (FK → `foods.id`) and `nested_recipe_id` (FK → `recipes.id`), both nullable. Exactly one must be set (enforced by `ck_recipe_ingredients_exactly_one_fk`). The existing `recipe_id` column identifies the parent recipe being defined. Direct self-reference (`nested_recipe_id = recipe_id`) is rejected by `ck_recipe_ingredients_no_self_ref`. Deep cycle prevention (A → B → A) is application-layer enforcement in the recipe management routes.

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

---

## Error shape

All API errors use one envelope, regardless of where they originate:

```json
{"error": {"code": "barcode_not_found", "message": "Human-readable string.", "details": {}}}
```

Implemented via a custom `PorquiloError` exception class in `core/errors.py` and a
single `@app.exception_handler` registration in `main.py`, plus handlers for
`RequestValidationError` and a catch-all `Exception`. This guarantees every failure
mode comes out in this shape — not just ones explicitly wrapped. Error `code` constants
live in `core/errors.py` alongside the class.

Auth-specific codes (added in Phase 1.5):

| Code | When |
|---|---|
| `invalid_credentials` | Username or password don't match |
| `token_revoked` | Token was explicitly revoked (logout or admin-forced) |
| `token_expired` | Token lifetime exceeded (tokens are non-expiring by default today) |
| `account_deactivated` | Admin deactivated this user |
| `insufficient_role` | A `member` hits an admin-only endpoint |
| `too_many_attempts` | Login lockout threshold hit |

Scale/BLE errors are explicitly out of scope — the server never sees a scale session.
A disconnected scale is detected client-side via CoreBluetooth and never produces a
server error response.

---

## Version endpoint

`GET /api/version` returns `{"version": "<semver>"}`. This is a public endpoint —
no auth required — so the mobile app can check server compatibility before presenting
the login screen. Pulled forward from Phase 5 into Phase 1.5 for this reason.