# Contributing to AMZ Ad Tracker

This is a local-first Amazon advertising tracking system (FastAPI + React + SQLite). The contributor base is small; this doc keeps it small-friendly.

## Project layout

```
amz-ad-tracker/
├── backend/              # FastAPI app, 18 routes, 14 services, 14 models
│   ├── api/              # Route modules (mounted via backend/api/__init__.py)
│   ├── services/         # Business logic (rule engine, KPI calc, backup, etc.)
│   ├── models/           # SQLAlchemy ORM models
│   ├── schemas/          # Pydantic request/response models
│   ├── utils/            # Amazon rule constants, encoding helper, parsers
│   └── config.py         # Settings (reads .env)
├── frontend/             # React 19 + TS + Antd 6 + ECharts + Vite 8
│   └── src/
│       ├── pages/        # 12 pages (Dashboard, Campaigns, ...)
│       ├── components/   # Shared UI (Layout, Sparkline, ...)
│       ├── hooks/        # Custom hooks (filters, theme, card order, column vis)
│       └── api/client.ts # Axios wrapper + error handling
├── tests/                # pytest (196 tests); no frontend tests yet
└── alembic/              # DB migrations
```

## Quick start (development)

### One-time setup

```bash
git clone https://github.com/Wekhoh/Zeoprix-AMZ-AD-Analysis.git
cd Zeoprix-AMZ-AD-Analysis

# 1. Backend deps
pip install -r requirements.txt -r requirements-dev.txt

# 2. Frontend deps
cd frontend && npm install && cd ..

# 3. Copy env template (optional — all settings have safe defaults)
cp .env.example .env

# 4. Install pre-commit (recommended)
pre-commit install
```

### Daily workflow

Run backend and frontend in two terminals:

```bash
# Terminal 1 — backend (http://127.0.0.1:8000)
python run.py

# Terminal 2 — frontend dev server (http://localhost:5173)
cd frontend && npm run dev
```

The Vite proxy in `frontend/vite.config.ts` forwards `/api/*` to `127.0.0.1:8000`. No CORS setup needed in dev.

## Running tests and checks

### Backend

```bash
# All tests (target <3s on M-class hardware)
python -m pytest tests/

# A single file, verbose
python -m pytest tests/test_backup_service.py -v

# Lint + format
python -m ruff check backend/ tests/
python -m ruff format backend/ tests/
```

### Frontend

```bash
cd frontend
npm run build       # tsc -b + vite build
npm run lint        # ESLint flat config
```

There are currently **0 frontend automated tests**. See the long-term roadmap for Vitest adoption.

## Making changes

### Before you edit

- Run the tests so you have a baseline. `196 passed in ~3s` is the expected state.
- Skim `README.md` and the hot files for the area you're touching:
  - `backend/services/<area>_service.py` — business logic
  - `frontend/src/pages/<Page>.tsx` — UI
  - `backend/models/<entity>.py` — schema

### PR hygiene

1. **Branch naming**: `feature/`, `fix/`, `refactor/`, `perf/`, `docs/`, `chore/` prefixes. Conventional Commits style in commit messages.
2. **≤ 3 file changes per PR** where possible. Split larger work into logical batches (see merged PRs `#8`–`#15` as examples).
3. **Every PR verifies** with:
   - `pytest tests/` green (backend)
   - `npm run build` exits 0 (frontend)
   - `npm run lint` clean or documented deltas
4. **Never commit** `.env`, real credentials, CSVs with real seller data, or files containing PII.
5. Prefer creating a new commit to amending a pushed one.

## Database migrations

SQLite + Alembic + a lightweight in-code migration list.

### Small schema nudges

`backend/database.py::_run_migrations()` contains idempotent `CREATE INDEX IF NOT EXISTS` / `ALTER TABLE ADD COLUMN` statements that run on startup. Use this for:

- New indexes
- New nullable columns on existing tables
- Other always-safe operations

### Larger model changes

Use Alembic for structural changes (new tables, NOT NULL columns, constraint changes, renames):

```bash
# 1. Edit backend/models/*.py
# 2. Generate revision
alembic revision --autogenerate -m "add <thing>"

# 3. Inspect the generated file under alembic/versions/ and adjust if needed
# 4. Apply
alembic upgrade head
```

Commit both the model change and the migration file in the same PR.

### Rolling back

```bash
alembic downgrade -1          # one revision back
alembic history               # view revision graph
```

If an in-code migration fails (e.g. a new index references a dropped column), edit `_run_migrations()` to skip it and open a follow-up cleanup PR.

## Imports and encoding

User-uploaded CSVs can be UTF-8 / UTF-8-BOM / GBK / GB2312. Always decode via `backend/utils/encoding_helper.py::decode_with_fallback()` rather than writing a new `for encoding in [...]` loop. The helper returns `None` on total failure so callers can decide how to surface the error.

## Style

- **Python**: ruff-enforced (`line-length=100`, rules `E/F/I/W`, ignore `E501`). Prefer type hints on public functions.
- **TypeScript**: strict mode on. Prefer `unknown` over `any`. Use `import type { ... }` for type-only imports. Antd 6 components; see `frontend/src/App.tsx` for theme token usage.
- **Comments**: default to no comments. Only document *why* something non-obvious is the way it is.

## Testing conventions

- Backend fixtures live in `tests/conftest.py`:
  - `db_session` — isolated in-memory SQLite with `PRAGMA foreign_keys=ON`
  - `client` — FastAPI `TestClient` with the session override already wired
  - `seed_campaign_data` — a reusable 2-campaign / 5-placement dataset
- For destructive endpoints (like `/api/settings/clear-data`), write assertions that prove both **what gets cleared** and **what must survive**. See `tests/test_data_manage.py` for the pattern.
- For security-sensitive paths (backup, export, anything touching the filesystem), include both the happy path and a "tampered record" case. See `tests/test_backup_service.py`.

## Release and update path

There's currently no formal release flow. For users updating from a previous version:

```bash
git pull
pip install -r requirements.txt   # picks up new deps
cd frontend && npm install        # picks up new frontend deps
alembic upgrade head              # applies any new schema migrations
cd .. && python run.py            # in-code migrations run on startup
```

Backups are created automatically before destructive operations, but keeping a manual copy of `data/tracker.db` before a major upgrade is wise.

## Asking for help

- Look at merged PRs for pattern examples (especially `#2`, `#3`, `#4`, `#7`, `#13` — representative of common change shapes).
- If something in this doc is wrong or out of date, please fix it in the same PR where you noticed. Docs are part of the code.
