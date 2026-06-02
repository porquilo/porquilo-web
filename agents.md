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

## Single-user

No multi-tenancy. No authentication layer in Phase 1. All data belongs to one user.