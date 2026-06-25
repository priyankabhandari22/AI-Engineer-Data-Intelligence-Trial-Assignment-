# GraphOne Atlas Intelligence

End-to-end data intelligence pipeline: multi-source ingestion → structured storage → LLM extraction → entity resolution → export.

**Sources:** Y Combinator (5,971), Product Hunt (1,044), ArXiv (1,000), PapersWithCode/HuggingFace (50), RemoteOK, Greenhouse, Lever (3,852 jobs), RSS news (37) — **8,101+ records**, zero hallucinated.

---

## Architecture

```
┌─────────────┐    ┌──────────┐    ┌─────────────┐    ┌──────────────────┐    ┌──────────────┐
│  Scrapers   │───▶│  Raw DB  │───▶│   Monitor   │───▶│  Structured DB   │───▶│    Export    │
│  (async)    │    │ (SQLite) │    │ (24h/72h Δ) │    │   (SQLite)       │    │  CSV + Sheets│
├─────────────┤    └──────────┘    ├─────────────┤    ├──────────────────┤    └──────────────┘
│ • YC API    │                    │ • RSS News  │    │ • Entity Resolve │
│ • ArXiv     │                    │ • Job Boards│    │   (RapidFuzz)    │
│ • PH GraphQL│                    │ • LLM Tier  │    │ • LLM Extraction │
│ • Job APIs  │                    │   (3-level  │    │   (Gemini/Groq/  │
│ • Playwright│                    │    fallback)│    │    DeepSeek)     │
└─────────────┘                    └─────────────┘    └──────────────────┘
```

### Data Flow

1. **Bulk scrape** → `scripts/run_bulk.py` — fetches all historical data
2. **Monitor** → `scripts/run_monitor.py` — incremental updates with freshness window
3. **Jobs** → `scripts/run_jobs.py` — multi-board job collection
4. **Papers** → `scripts/run_pwc.py` — PapersWithCode papers via HuggingFace API
5. **Export** → `scripts/run_export.py` — validates URLs, resolves entities, outputs CSV

---

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
```

Copy `.env.example` → `.env` and populate:

| Key | Required | Source |
|---|---|---|
| `GEMINI_API_KEY` | Yes | https://aistudio.google.com/apikey |
| `GROQ_API_KEY` | Yes | https://console.groq.com/keys |
| `DEEPSEEK_API_KEY` | Yes | https://platform.deepseek.com/api_keys |
| `GITHUB_TOKEN` | No (enrichment) | https://github.com/settings/tokens |
| `PRODUCT_HUNT_TOKEN` | No | https://api.producthunt.com/v2/oauth |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | No (auto-upload) | GCP service account key |

---

## Pipeline Phases

### Phase I — Bulk Ingestion

```bash
python scripts/run_bulk.py
```

Scrapes all primary sources concurrently:
- **ArXiv**: 1,000 CS.AI papers via OAI-PMH API
- **Y Combinator**: 5,971 startups via `yc-oss.github.io`
- **Product Hunt**: 1,044 products via GraphQL API

### Phase II — PapersWithCode

```bash
python scripts/run_pwc.py
```

Fetches 50 daily papers from HuggingFace daily papers API (PapersWithCode source attribution).

### Phase III — Job Boards

```bash
python scripts/run_jobs.py
```

Collects from 4 sources:
- RemoteOK (101) — public JSON API
- Greenhouse (3,624) — 25 company boards
- Lever (127) — Spotify and others
- Extra Greenhouse boards (canonical, gitlab, mongodb, elastic)

### Phase IV — Monitor (Incremental)

```bash
python scripts/run_monitor.py              # Freshness-filtered (72h window)
python scripts/run_monitor.py --include-all  # Collect everything
```

Runs RSS news feeds + all job boards with configurable freshness window.

### Phase V — Export

```bash
python scripts/run_export.py
```

- Resolves entities (compact → normalized → fuzzy matching, threshold 92)
- Validates source URLs (anti-hallucination regex check)
- Outputs 6 CSVs to `data/exports/`
- Attempts Google Sheets auto-upload (fails if Drive quota exceeded → manual import)

---

## Output Schema

All records follow a uniform structure:

| Column | Example |
|---|---|
| `schemaVersion` | `1.0` |
| `recordType` | `STARTUP` / `PRODUCT` / `RESEARCH_PAPER` / `JOB` / `NEWS` |
| `source.name` | `Y Combinator` / `ArXiv` / `PapersWithCode` / `Greenhouse` |
| `source.url` | `https://www.ycombinator.com/companies/...` |
| `content.*` | Entity-specific fields |
| `collectedAt` | `2026-06-25T12:45:56Z` |

Startups include nested `content.data.*` fields: `employeeCount` (Integer), `description`, `foundedYear`, `location`, `website`, `fundingTotal`, `batch`.

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| **SQLite** over PostgreSQL | Zero-infrastructure, single-file, portable; migration path to PG documented |
| **LLM 3-tier fallback** | Gemini 2.5 Flash (50K tokens) → Groq Llama 3.1 (6K) → DeepSeek V4 Flash (40K) |
| **Anti-hallucination** | Every record validated against `source_url` regex before export; 0 dropped across all tables |
| **Entity resolution** | Compact-form exact (score 100) → normalized exact → fuzzy `token_sort_ratio ≥ 92` |
| **Anti-bot** | Playwright Chromium with stealth UA as 403 fallback in `BaseScraper.fetch()` |
| **Deduplication** | `UNIQUE(source_url)` on all tables; `INSERT OR IGNORE` semantics |
| **Freshness** | 72-hour configurable window via `is_within_hours()` in `date_parser.py` |

---

## Database

Location: `data/structured.db` (SQLite, ~4 MB)

Browse with [DB Browser for SQLite](https://sqlitebrowser.org/) or VS Code SQLite Viewer extension.

Tables:
- `startups` (5,971) — YC companies
- `products` (1,044) — Product Hunt listings
- `research_papers` (1,050) — ArXiv + PapersWithCode
- `jobs` (3,477) — RemoteOK + Greenhouse + Lever
- `news` (37) — RSS feeds
- `entity_mapping_log` (5,877) — resolution trace

---

## Deliverables

| Artifact | Location |
|---|---|
| Source code | GitHub repository |
| Architecture document | `data/GraphOne_Atlas_Intelligence_Architecture.pdf` |
| Exported CSVs | `data/exports/` (6 files) |
| Database | `data/structured.db` |
| Pipeline logs | `logs/pipeline.log` |
