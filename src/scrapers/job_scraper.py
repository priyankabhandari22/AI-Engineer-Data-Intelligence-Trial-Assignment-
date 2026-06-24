import aiohttp
from datetime import datetime
from loguru import logger
from .base_scraper import BaseScraper


class JobScraper(BaseScraper):

    async def fetch_remoteok_jobs(self) -> list[dict]:
        url = "https://remoteok.com/api"
        async with aiohttp.ClientSession() as session:
            data = await self.fetch_json(session, url)

        if not data or not isinstance(data, list):
            logger.error("Failed to fetch RemoteOK jobs")
            return []

        records = []
        for item in data:
            if not isinstance(item, dict) or item.get("id") == "placeholder":
                continue
            record = {
                "schemaVersion": "1.0",
                "recordType": "JOB",
                "source": {"name": "RemoteOK", "url": item.get("url")},
                "content": {
                    "company": item.get("company"),
                    "role_title": item.get("position"),
                    "role_family": None,
                    "date": item.get("date"),
                    "is_remote": True,
                    "location": "Remote",
                    "salary_range": item.get("salary"),
                },
                "collectedAt": datetime.utcnow().isoformat() + "Z",
            }
            records.append(record)

        logger.info(f"Fetched {len(records)} jobs from RemoteOK")
        return records

    async def fetch_greenhouse_jobs(self, board_token: str = "greenhouse") -> list[dict]:
        url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
        async with aiohttp.ClientSession() as session:
            data = await self.fetch_json(session, url)

        if not data:
            return []

        records = []
        for job in data.get("jobs", []):
            record = {
                "schemaVersion": "1.0",
                "recordType": "JOB",
                "source": {"name": "Greenhouse", "url": job.get("absolute_url")},
                "content": {
                    "company": board_token,
                    "role_title": job.get("title"),
                    "role_family": None,
                    "date": job.get("updated_at"),
                    "is_remote": None,
                    "location": job.get("location", {}).get("name") if job.get("location") else None,
                    "salary_range": None,
                },
                "collectedAt": datetime.utcnow().isoformat() + "Z",
            }
            records.append(record)

        logger.info(f"Fetched {len(records)} jobs from Greenhouse/{board_token}")
        return records
