# GraphOne Intelligence Pipeline

End-to-end data intelligence system: multi-source ingestion → structured storage → LLM extraction → entity resolution → CSV/Sheets export. **8,101+ records across 6 source types, zero hallucinated.**

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        INGESTION LAYER                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────┐ │
│  │ YC API   │  │  ArXiv   │  │ProductHunt│  │Job Boards│  │ RSS  │ │
│  │(REST)    │  │ (OAI-PMH)│  │ (GraphQL) │  │ (REST)   │  │ Atom │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──┬───┘ │
│       │ asyncio     │ asyncio     │ asyncio     │ asyncio    │      │
└───────┼─────────────┼─────────────┼─────────────┼────────────┼──────┘
        ▼             ▼             ▼             ▼            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      STORAGE LAYER                                  │
│              ┌──────────────────────────────┐                       │
│              │      structured.db (SQLite)   │                       │
│              │  ┌──────────┐ ┌────────────┐ │                       │
│              │  │  raw_*   │ │  startups  │ │                       │
│              │  │  tables  │ │  products  │ │                       │
│              │  │          │ │  papers    │ │                       │
│              │  │          │ │  jobs      │ │                       │
│              │  │          │ │  news      │ │                       │
│              │  │          │ │  entity_log│ │                       │
│              │  └──────────┘ └────────────┘ │                       │
│              └──────────────────────────────┘                       │
└─────────────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      PROCESSING LAYER                               │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────────────┐  │
│  │ LLM Extraction │──▶Entity Resolution│──▶  Export & Validate   │  │
│  │ Gemini → Groq  │  │Compact→Norm→Fuzz│  │  URL regex check    │  │
│  │ → DeepSeek     │  │(threshold 92)   │  │  → CSV + Sheets     │  │
│  └────────────────┘  └────────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.13 |
| **Async HTTP** | `aiohttp` + `asyncio` |
| **Browser Automation** | Playwright Chromium (403 fallback) |
| **LLM** | Gemini 2.5 Flash → Groq Llama 3.1 → DeepSeek V4 Flash |
| **Entity Resolution** | RapidFuzz (`token_sort_ratio`, threshold 92) |
| **Database** | SQLite (single-file, zero-infrastructure) |
| **Export** | pandas CSV + gspread (Google Sheets) |
| **Date Parsing** | `dateutil` + custom relative-date parser |

---

## Data Pipeline / Sources

| Source | Type | Method | Records | Frequency |
|---|---|---|---|---|
| **Y Combinator** | Startups | `yc-oss.github.io` REST API | 5,971 | Bulk |
| **Product Hunt** | Products | GraphQL API (paginated) | 1,044 | Bulk |
| **ArXiv** | Research Papers | OAI-PMH API (batched) | 1,000 | Bulk |
| **PapersWithCode / HuggingFace** | Research Papers | HF Daily Papers API | 50 | Daily |
| **RemoteOK** | Jobs | Public JSON API | 101 | Monitor |
| **Greenhouse** | Jobs | Boards API (25 companies) | 3,624 | Monitor |
| **Lever** | Jobs | Postings API (multi-board) | 127 | Monitor |
| **RSS News Feeds** | News | feedparser (4 sources) | 37 | Monitor |

Every record traces to a valid `source_url` — zero hallucinated data.

---

## Prerequisites

- Python 3.10+
- [Playwright Chromium](https://playwright.dev/python/) (`playwright install chromium`)
- API keys for LLM extraction (see Configuration)

---

## Configuration

```bash
cp .env.example .env
```

| Key | Required | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | Yes | Primary LLM extraction tier |
| `GROQ_API_KEY` | Yes | Secondary LLM fallback |
| `DEEPSEEK_API_KEY` | Yes | Tertiary LLM fallback |
| `GITHUB_TOKEN` | Optional | GitHub star enrichment |
| `PRODUCT_HUNT_TOKEN` | Optional | Product Hunt API access |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Optional | Google Sheets auto-upload |

LLM extraction degrades gracefully — missing keys skip that tier rather than failing.

---

## Google Sheets Setup

1. **Create spreadsheet** named `GraphOne Atlas Intelligence`
2. **Create 6 tabs** with these exact names:
   - `Startups`
   - `Products`
   - `Research Papers`
   - `Jobs`
   - `News`
   - `Entity Mapping Log`
3. **Auto-upload**: Place GCP service account JSON at `service-account.json` and set `GOOGLE_SERVICE_ACCOUNT_JSON` in `.env`
4. **Manual fallback**: Import the 6 CSVs from `data/exports/` into corresponding tabs

> If the service account Drive quota is exceeded, the CSVs are always saved locally as a fallback.

---

## Running the Pipeline

```bash
# Phase I — Bulk Ingestion
# Scrapes YC + ArXiv + Product Hunt concurrently
python scripts/run_bulk.py

# Phase II — PapersWithCode
# Fetches daily papers from HuggingFace API
python scripts/run_pwc.py

# Phase III — Job Boards
# Collects from RemoteOK + Greenhouse + Lever
python scripts/run_jobs.py

# Phase IV — Incremental Monitor
# Freshness-filtered (72h default window)
python scripts/run_monitor.py
# Bypass freshness filter to collect everything
python scripts/run_monitor.py --include-all

# Phase V — Export
# Entity resolution + URL validation + CSV/Sheets
python scripts/run_export.py
```

---

## Expected Runtime

| Step | Duration | Notes |
|---|---|---|
| `run_bulk.py` | ~5-8 min | ArXiv rate-limiting (3s delay between batches) |
| `run_pwc.py` | ~2-5 sec | Single API call |
| `run_jobs.py` | ~2-3 min | 30+ API calls across 4 boards |
| `run_monitor.py` | ~30-60 sec | Lightweight feed fetch |
| `run_export.py` | ~2-5 sec | In-memory pandas operations |

**Total pipeline**: ~10-12 minutes end-to-end.

---

## Output Schema

All records follow a uniform structure with source traceability:

| Column | Type | Example |
|---|---|---|
| `schemaVersion` | String | `1.0` |
| `recordType` | String | `STARTUP` |
| `source.name` | String | `Y Combinator` |
| `source.url` | String (validated) | `https://...` |
| `content.*` | Mixed | Entity-specific fields |
| `collectedAt` | ISO 8601 | `2026-06-25T12:45:56Z` |

### Startups (`content.data.*`)

| Field | Type | Populated |
|---|---|---|
| `entityName` | String | 5,971 / 5,971 |
| `description` | String | All |
| `employeeCount` | Integer | Most |
| `foundedYear` | Integer | Varies |
| `location` | String | Varies |
| `website` | String | Most |
| `fundingTotal` | String | Varies |
| `batch` | String | 5,970 / 5,971 |

### Products

| Field | Populated |
|---|---|
| `productName` | 1,044 / 1,044 |
| `startupName` | All |
| `description` | All |
| `pricingModel` | Varies |
| `website` | Most |
| `category` | Most |

### Research Papers

| Field | Populated |
|---|---|
| `title` | 1,050 / 1,050 |
| `authors` | All |
| `paper_url` | All |
| `github_url` | Varies (enriched) |
| `github_stars` | Varies |

### Jobs

| Field | Populated |
|---|---|
| `company` | 3,477 / 3,477 |
| `role_title` | All |
| `is_remote` | Boolean |
| `location` | Varies |
| `salary_range` | Varies |

---

## Entity Resolution

Two-pass engine in `src/entity_resolution/resolver.py`:

```
Input name
  │
  ├── Pass 1: Compact exact match (remove spaces/dashes, lowercase)
  │     Score = 100? ──YES──▶ return canonical name
  │     No
  │
  ├── Pass 2: Normalized exact match (lowercase + strip)
  │     Score = 100? ──YES──▶ return canonical name
  │     No
  │
  └── Pass 3: Fuzzy match (RapidFuzz token_sort_ratio, threshold 92)
        Match ≥ 92? ──YES──▶ return canonical name
        No
        │
        ▼
  Return input unchanged
```

**Examples:**
- `"Open AI"` → compact → `"openai"` → exact match `"OpenAI"` (score 100)
- `"Canvass"` → fuzzy → no match (threshold 92 prevents false positive)
- `"Deel"` → fuzzy ≠ `"DeepL"` (score below 92, prevented)
- `"Anthropic PBC"` → normalized strips `" PBC"` → matches `"Anthropic"`

---

## LLM Extraction Chain

Three-tier fallback for structured data extraction:

```
Raw text
  │
  ├── Tier 1: Gemini 2.5 Flash (50K tokens)
  │     Success? ──YES──▶ Done
  │     No (503/429 retry)
  │
  ├── Tier 2: Groq Llama 3.1 8B (6K tokens)
  │     Success? ──YES──▶ Done
  │     No
  │
  └── Tier 3: DeepSeek V4 Flash (40K tokens)
        Success? ──YES──▶ Done
        No
        │
        ▼
  Log warning, skip record
```

- Exponential backoff (2s-10s) for 429 (rate limit) and 503 (unavailable)
- Each tier uses a different model provider to maximize coverage
- Token limits prevent truncation; content is chunked if needed

---

## Freshness Guarantee (News + Jobs)

```python
# src/freshness/date_parser.py
is_within_hours(dt, hours=72)  # Configurable window
```

- Each news/job record carries a `collectedAt` timestamp
- Monitor script filters by `is_within_hours()` before insert
- RSS dates: relative patterns parsed (`"2 hours ago"`, `"yesterday"`)
- Standard dates: parsed via `dateutil.parser` with UTC normalization
- `--include-all` bypasses freshness filter for initial backfill
- `UNIQUE(source_url)` prevents duplicates on re-run

---

## Project Structure

```
graphone-pipeline/
├── config/
│   ├── settings.py
│   └── __init__.py
├── scripts/
│   ├── run_bulk.py              # Phase I: Bulk scrape
│   ├── run_pwc.py               # Phase II: PapersWithCode
│   ├── run_jobs.py              # Phase III: Job boards
│   ├── run_monitor.py           # Phase IV: Incremental
│   ├── run_export.py            # Phase V: Export
│   └── generate_pdf.py          # Architecture PDF
├── src/
│   ├── scrapers/
│   │   ├── base_scraper.py      # Async HTTP + Playwright + retry
│   │   ├── startup_scraper.py   # Y Combinator API
│   │   ├── product_scraper.py   # Product Hunt GraphQL
│   │   ├── paper_scraper.py     # ArXiv + HF daily papers
│   │   ├── job_scraper.py       # RemoteOK + Greenhouse + Lever
│   │   ├── news_scraper.py      # RSS feedparser + HN API
│   │   └── github_enricher.py   # GitHub star lookup
│   ├── storage/
│   │   └── database.py          # SQLite schema + inserts
│   ├── freshness/
│   │   └── date_parser.py       # Date parsing + freshness
│   ├── llm/
│   │   ├── orchestrator.py      # 3-tier fallback chain
│   │   ├── validators.py        # Output validation
│   │   ├── prompts.py           # Extraction prompts
│   │   └── chunker.py           # Text chunking
│   ├── entity_resolution/
│   │   ├── resolver.py          # Compact→norm→fuzzy pipeline
│   │   ├── normalizer.py        # Text normalization
│   │   └── seed_entities.py     # Known entities
│   └── output/
│       └── sheets_uploader.py   # Google Sheets upload
├── data/
│   ├── structured.db            # SQLite (~4 MB)
│   ├── exports/                 # 6 CSV files
│   ├── sheets_ready/
│   └── GraphOne_Atlas_Intelligence_Architecture.pdf
├── logs/
│   └── pipeline.log
├── .env.example
├── requirements.txt
└── README.md
```

---

## Deliverables

| Artifact | Path |
|---|---|
| Source code | GitHub repository |
| Architecture document | `data/GraphOne_Atlas_Intelligence_Architecture.pdf` |
| Exported CSVs | `data/exports/` (6 files) |
| SQLite database | `data/structured.db` |
| Pipeline logs | `logs/pipeline.log` |
