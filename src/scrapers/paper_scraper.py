import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from datetime import datetime
from loguru import logger
from .base_scraper import BaseScraper


class PaperScraper(BaseScraper):
    ARXIV_BASE = "http://export.arxiv.org/api/query"
    PWC_BASE = "https://paperswithcode.com/api/v1"

    async def fetch_arxiv_papers(self, category="cs.AI", max_results=1000) -> list[dict]:
        papers = []
        batch_size = 100

        async with aiohttp.ClientSession() as session:
            for start in range(0, max_results, batch_size):
                url = (f"{self.ARXIV_BASE}?search_query=cat:{category}"
                       f"&start={start}&max_results={batch_size}"
                       f"&sortBy=submittedDate&sortOrder=descending")

                html = await self.fetch(session, url)
                if not html:
                    continue

                root = ET.fromstring(html)
                ns = {'atom': 'http://www.w3.org/2005/Atom'}

                for entry in root.findall('atom:entry', ns):
                    paper_url = entry.find('atom:id', ns).text.strip()
                    paper = {
                        "schemaVersion": "1.0",
                        "recordType": "RESEARCH_PAPER",
                        "source": {"name": "ArXiv", "url": paper_url},
                        "content": {
                            "title": entry.find('atom:title', ns).text.strip(),
                            "authors": [
                                a.find('atom:name', ns).text
                                for a in entry.findall('atom:author', ns)
                            ],
                            "paper_url": paper_url,
                            "published_date": entry.find('atom:published', ns).text,
                            "github_url": None,
                            "github_stars": None,
                        },
                        "collectedAt": datetime.utcnow().isoformat() + "Z"
                    }
                    papers.append(paper)

                logger.info(f"Fetched {len(papers)} papers so far...")
                await asyncio.sleep(3)

        return papers

    async def enrich_with_github(self, papers: list[dict]) -> list[dict]:
        async with aiohttp.ClientSession() as session:
            for paper in papers:
                title = paper["content"]["title"]
                url = f"{self.PWC_BASE}/papers/?title={title[:50]}"

                try:
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data.get("results"):
                                result = data["results"][0]
                                paper["content"]["github_url"] = result.get("repository", {}).get("url")
                except Exception as e:
                    logger.warning(f"PwC lookup failed for {title}: {e}")

                await asyncio.sleep(0.5)

        return papers
