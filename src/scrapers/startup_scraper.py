import aiohttp
import asyncio
from datetime import datetime
from loguru import logger
from .base_scraper import BaseScraper


class StartupScraper(BaseScraper):
    YC_API = "https://yc-oss.github.io/api/companies/all.json"

    async def fetch_yc_startups(self) -> list[dict]:
        async with aiohttp.ClientSession() as session:
            data = await self.fetch_json(session, self.YC_API)
            if not data:
                logger.error("Failed to fetch YC companies")
                return []

        records = []
        for item in data:
            record = {
                "schemaVersion": "1.0",
                "recordType": "STARTUP",
                "source": {
                    "name": "Y Combinator",
                    "url": item.get("url") or "https://www.ycombinator.com/companies",
                },
                "content": {
                    "entityName": item.get("name"),
                    "data": {
                        "description": item.get("one_liner") or item.get("long_description"),
                        "foundedYear": item.get("year_founded") or item.get("founded"),
                        "employeeCount": item.get("team_size"),
                        "location": item.get("location"),
                        "website": item.get("website"),
                        "fundingTotal": None,
                        "batch": item.get("batch"),
                    }
                },
                "collectedAt": datetime.utcnow().isoformat() + "Z"
            }
            records.append(record)

        logger.info(f"Fetched {len(records)} YC startups")
        return records

    async def fetch_crunchbase_startups(self, limit: int = 500) -> list[dict]:
        records = []
        # Crunchbase free pages — simple HTML scraping per README
        base_url = "https://www.crunchbase.com/discover/organization.companies"
        urls = [f"{base_url}?page={i}" for i in range(1, (limit // 20) + 1)]

        async with aiohttp.ClientSession() as session:
            for url in urls:
                html = await self.fetch(session, url)
                if html:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html, "html.parser")
                    # NOTE: Crunchbase uses heavy JS; this is best-effort.
                    # YC API is the primary source (4000+ records).
                    pass
                await asyncio.sleep(1)

        return records
