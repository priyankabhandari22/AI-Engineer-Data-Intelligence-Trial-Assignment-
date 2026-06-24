# GraphOne Atlas Intelligence

Multi-stage data pipeline: scrape → store → LLM extract → entity resolve → export.

## Architecture

```
Scrapers ──► Raw DB ──► Monitor ──► LLM Extract ──► Structured DB ──► Entity Resolve ──► Export/Sheets
(ArXiv,      (SQLite)    (24h cycle)   (Gemini/Groq/                    (RapidFuzz)      (CSV +
 YC, PH,                  --include-     DeepSeek                                          Google
 RSS,                      all flag)     fallback)                                         Sheets)
 RemoteOK)
```

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
```

Copy `.env.example` to `.env` and fill in your API keys:

| Key | Source |
|---|---|
| `GEMINI_API_KEY` | https://aistudio.google.com/apikey |
| `GROQ_API_KEY` | https://console.groq.com/keys |
| `DEEPSEEK_API_KEY` | https://platform.deepseek.com/api_keys |
| `PRODUCT_HUNT_TOKEN` | https://api.producthunt.com/v2/oauth |
| `GITHUB_TOKEN` | https://github.com/settings/tokens |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Path to GCP service account key (for Sheets) |

## Running the Pipeline

```bash
# Phase I: Bulk scrape (ArXiv 1K + YC 6K + Product Hunt 1K)
python scripts/run_bulk.py

# Phase II: Monitor (daily incremental — RSS news + RemoteOK jobs)
python scripts/run_monitor.py          # 24h freshness filter only
python scripts/run_monitor.py --include-all  # Save everything (for testing)

# Phase III: Export + Entity Resolution
python scripts/run_export.py
```

Output CSVs are saved to `data/exports/`. Import them manually to Google Sheets
(the auto-upload fails if the service account Drive quota is exceeded).

## Key Design Decisions

- **SQLite** over PostgreSQL: zero-infrastructure, single-file DB, clean migration path
- **LLM fallback**: Gemini 2.5 Flash (50K tokens) → Groq Llama 3.1 8B (6K) → DeepSeek V4 Flash (40K)
- **Anti-hallucination**: Every record validated against `source_url` regex before export
- **Entity resolution**: Compact-form exact match → normalized exact match → fuzzy (token_sort_ratio ≥ 92)
- **Anti-bot**: Playwright Chromium with stealth user-agent as 403 fallback in BaseScraper
- **Dedup**: `UNIQUE(source_url)` on all tables; `--include-all` flag for test mode
