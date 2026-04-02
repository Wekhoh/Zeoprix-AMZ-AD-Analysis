# AMZ Ad Tracker

> Amazon Advertising Intelligent Tracking System

A professional-grade, local-first web application for tracking and analyzing Amazon PPC advertising campaigns. Built with FastAPI + React + SQLite.

**Zero monthly fees. Your data stays on your machine.**

---

## Features

### Core Tracking
- **Multi-ad type support** — SP, SB, SD, SBV campaign tracking
- **CSV/TXT import** — Upload Amazon placement reports and operation logs with 3-step preview flow
- **Smart deduplication** — Automatic duplicate detection and attribution window data correction

### Analytics & Intelligence
- **Dashboard** — KPI cards, daily trend charts, status pie chart, conversion funnel, alerts
- **4-Bucket search term analysis** — Winners / Potential / Money Pits / Low Data classification
- **Smart suggestions** — 7 rule types with bidding strategy awareness and Buy Box loss detection
- **Period comparison** — Side-by-side KPI comparison with color-coded deltas
- **Rule engine** — 7 preset rules + custom rules with manual evaluation
- **Category benchmarks** — Compare your KPIs against 9 industry categories
- **Excel report** — 6-sheet professional report with cross-analysis pivot tables

### Amazon Rules Integration
- **Attribution window awareness** — SP 7-day vs SB/SD 14-day attribution labeling
- **CPC stacking calculator** — Placement adjustment x Dynamic bidding = multiplicative
- **Bidding strategy-aware advice** — Different recommendations for Fixed / Down Only / Up+Down
- **72-hour negative keyword buffer** — Warning on Money Pits actions
- **Ad eligibility checklist** — Buy Box, inventory, listing compliance checks

### Professional UX
- **Dark / Light / System theme** — Smooth transitions, persistent preference
- **Ctrl+K command palette** — Quick navigation and actions
- **Collapsible sidebar** — Icon mode for more screen space
- **Breadcrumb navigation** — Full path tracking across all pages
- **Page-level help** — Contextual guidance on every page
- **First-use onboarding** — 4-step guided setup for new users
- **Error boundary** — Graceful error handling, no white screens
- **Server-side pagination** — Efficient loading for large datasets

### Engineering
- **34 automated tests** — CSV parser, KPI calculator, date parser, import API
- **Structured logging** — Rotating file logs with request ID tracing
- **15 database indexes** — Optimized query performance at scale
- **Backup system** — Auto pre-import backup, integrity verification, one-click restore
- **Docker ready** — Multi-stage Dockerfile + docker-compose.yml

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + SQLAlchemy + SQLite (WAL mode) |
| Frontend | React 19 + TypeScript + Ant Design 6 + ECharts |
| Build | Vite 8 |
| Testing | pytest (34 tests) |
| Container | Docker + docker-compose |

---

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+

### Installation

```bash
git clone https://github.com/Wekhoh/Zeoprix-AMZ-AD-Analysis.git
cd Zeoprix-AMZ-AD-Analysis

# Backend
pip install -r requirements.txt

# Frontend
cd frontend && npm install && npm run build && cd ..

# Launch
python run.py
```

Browser opens automatically at `http://127.0.0.1:8000`.

### Docker

```bash
docker compose up
```

---

## Project Structure

```
amz-ad-tracker/
├── backend/
│   ├── api/            # 15 route modules (45+ endpoints)
│   ├── models/         # 14 SQLAlchemy models (16 tables)
│   ├── services/       # 15 business logic services
│   ├── schemas/        # Pydantic validation models
│   └── utils/          # Amazon rules, parsers
├── frontend/src/
│   ├── pages/          # 12 page components
│   ├── components/     # 9 shared components
│   ├── hooks/          # 3 custom hooks
│   └── utils/          # Chart theme, CSV export
├── tests/              # 34 pytest tests
├── Dockerfile
└── docker-compose.yml
```

---

## Pages

| Page | Route | Description |
|------|-------|------------|
| Dashboard | `/` | KPI overview, trends, funnel, alerts, benchmarks |
| Import | `/import` | 3-step CSV/TXT upload with preview |
| Campaigns | `/campaigns` | SP/SB/SD/SBV type filtering |
| Campaign Detail | `/campaigns/:id` | Trends, placements, logs, notes |
| Placements | `/placements` | Paginated table + filters + CSV export |
| Operation Logs | `/operation-logs` | Paginated change history |
| Summaries | `/summaries` | By date/campaign/placement + Excel export |
| Comparison | `/analysis` | Period-over-period KPI analysis |
| Search Terms | `/search-terms` | 4-Bucket analysis with target ACOS |
| Suggestions | `/suggestions` | Strategy-aware recommendations |
| Rules | `/rules` | 7 presets + custom automation |
| Settings | `/settings` | Backup, costs, sales, import history |

---

## Tests

```bash
python -m pytest tests/ -v
```

```
34 passed in 0.15s
```

---

## License

MIT
