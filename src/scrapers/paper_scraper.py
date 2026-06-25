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

    async def fetch_hf_daily_papers(self, limit: int = 100) -> list[dict]:
        papers = []
        async with aiohttp.ClientSession(headers={"Accept": "application/json"}) as session:
            url = "https://huggingface.co/api/daily_papers"
            async with session.get(url) as resp:
                if resp.status != 200:
                    logger.error(f"HF daily papers API returned {resp.status}")
                    return []
                data = await resp.json()
            for item in data[:limit]:
                paper_data = item.get("paper", item)
                title = paper_data.get("title", "")
                paper_url = f"https://arxiv.org/abs/{paper_data.get('id', '')}"
                pwc_url = f"https://paperswithcode.com/paper/{paper_data.get('id', '')}"
                authors = paper_data.get("authors") or paper_data.get("author_list", [])
                if isinstance(authors, list) and all(isinstance(a, dict) for a in authors):
                    authors = [a.get("name", "") for a in authors]
                paper = {
                    "schemaVersion": "1.0",
                    "recordType": "RESEARCH_PAPER",
                    "source": {"name": "PapersWithCode", "url": pwc_url},
                    "content": {
                        "title": title,
                        "authors": authors,
                        "paper_url": paper_url,
                        "published_date": paper_data.get("published_at") or paper_data.get("pubdate"),
                        "github_url": paper_data.get("url") or None,
                        "github_stars": None,
                    },
                    "collectedAt": datetime.utcnow().isoformat() + "Z",
                }
                papers.append(paper)
        logger.info(f"Fetched {len(papers)} papers from HuggingFace daily papers API")
        return papers
