# Porquilo

Self-hosted, single-user (for now) nutrition tracker. AGPL licensed.

---

## Stack

- **Backend:** FastAPI (Python), SQLModel, Alembic — `server/`
- **Frontend:** Vite + React + TypeScript — `web-app/`
- **Database:** SQLite in dev, PostgreSQL in prod — `DATABASE_URL` environment variable controls which

## Monorepo structure

```
server/        ← FastAPI API server (see server/agents.md)
web-app/  ← React frontend (see web-app/agents.md)
```

## Product principles

- Trusted kitchen companion, never a fitness app — no goal rings, no streaks, no gamification
- Sentence case throughout the UI
- Self-hosters are first-class citizens — feature parity with any hosted tier
- Open Food Facts contribution loop is a core part of the product identity

## Users & auth

Household-scale multi-user: separate diaries per person, one shared server instance.
Real per-user accounts from the start — no shared server password. The first account
created is the admin; subsequent accounts are created by the admin via the web dashboard.
`foods`, `recipes`, and `meals` are global to the instance — visible to all users.
All other data (`log_entries`, `body_metrics`, goals) is scoped per user.