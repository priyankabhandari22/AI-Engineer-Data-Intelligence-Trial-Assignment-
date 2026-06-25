import aiohttp
from datetime import datetime
from loguru import logger
from .base_scraper import BaseScraper


class JobScraper(BaseScraper):

    REMOTEOK_API = "https://remoteok.com/api"

    GREENHOUSE_BOARDS = [
        "greenhouse", "stripe", "airbnb", "lyft", "coinbase",
        "pinterest", "dropbox", "spotify", "doordash", "instacart",
        "reddit", "quora", "twilio", "datadog", "hashicorp",
    ]

    LEVER_BOARDS = [
        "spotify", "asana", "gusto", "carta", "brex",
        "notion", "linear", "vercel", "netlify", "supabase",
    ]

    async def fetch_remoteok_jobs(self) -> list[dict]:
        async with aiohttp.ClientSession() as session:
            data = await self.fetch_json(session, self.REMOTEOK_API)
        if not data or not isinstance(data, list):
            logger.error("Failed to fetch RemoteOK jobs")
            return []
        records = []
        for item in data:
            if not isinstance(item, dict) or item.get("id") == "placeholder":
                continue
            records.append(self._make_record("RemoteOK", item.get("url"), {
                "company": item.get("company"),
                "role_title": item.get("position"),
                "role_family": None,
                "date": item.get("date"),
                "is_remote": True,
                "location": "Remote",
                "salary_range": item.get("salary"),
            }))
        logger.info(f"Fetched {len(records)} jobs from RemoteOK")
        return records

    async def fetch_all_greenhouse_jobs(self) -> list[dict]:
        all_records = []
        for board in self.GREENHOUSE_BOARDS:
            try:
                records = await self._fetch_single_greenhouse(board)
                all_records.extend(records)
            except Exception as e:
                logger.warning(f"Greenhouse/{board} failed: {e}")
        logger.info(f"Fetched {len(all_records)} jobs from Greenhouse ({len(self.GREENHOUSE_BOARDS)} boards)")
        return all_records

    async def _fetch_single_greenhouse(self, board_token: str) -> list[dict]:
        url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
        async with aiohttp.ClientSession() as session:
            data = await self.fetch_json(session, url)
        if not data:
            return []
        records = []
        for job in data.get("jobs", []):
            records.append(self._make_record("Greenhouse", job.get("absolute_url"), {
                "company": board_token,
                "role_title": job.get("title"),
                "role_family": None,
                "date": job.get("updated_at"),
                "is_remote": None,
                "location": job.get("location", {}).get("name") if job.get("location") else None,
                "salary_range": None,
            }))
        return records

    async def fetch_all_lever_jobs(self) -> list[dict]:
        all_records = []
        for board in self.LEVER_BOARDS:
            try:
                records = await self._fetch_single_lever(board)
                all_records.extend(records)
            except Exception as e:
                logger.warning(f"Lever/{board} failed: {e}")
        logger.info(f"Fetched {len(all_records)} jobs from Lever ({len(self.LEVER_BOARDS)} boards)")
        return all_records

    async def _fetch_single_lever(self, board_token: str) -> list[dict]:
        url = f"https://api.lever.co/v0/postings/{board_token}?mode=json"
        async with aiohttp.ClientSession() as session:
            data = await self.fetch_json(session, url)
        if not data or not isinstance(data, list):
            return []
        records = []
        for job in data:
            records.append(self._make_record("Lever", job.get("hostedUrl"), {
                "company": board_token,
                "role_title": job.get("text"),
                "role_family": job.get("categories", {}).get("team") if job.get("categories") else None,
                "date": job.get("createdAt"),
                "is_remote": None,
                "location": job.get("categories", {}).get("location") if job.get("categories") else None,
                "salary_range": None,
            }))
        return records

    async def fetch_more_greenhouse_boards(self) -> list[dict]:
        extra_boards = [
            "canonical", "gitlab", "zendesk", "sentry", "datadog",
            "mongodb", "elastic", "snowflake", "confluent", "digitalocean",
        ]
        all_records = []
        for board in extra_boards:
            try:
                records = await self._fetch_single_greenhouse(board)
                all_records.extend(records)
            except Exception as e:
                logger.warning(f"Greenhouse/{board} failed: {e}")
        logger.info(f"Fetched {len(all_records)} extra jobs from Greenhouse ({len(extra_boards)} extra boards)")
        return all_records

    def _make_record(self, source_name: str, url: str | None, content: dict) -> dict:
        return {
            "schemaVersion": "1.0",
            "recordType": "JOB",
            "source": {"name": source_name, "url": url or ""},
            "content": content,
            "collectedAt": datetime.utcnow().isoformat() + "Z",
        }
