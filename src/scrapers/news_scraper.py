import asyncio
import feedparser
from datetime import datetime
from loguru import logger
from .base_scraper import BaseScraper


class NewsScraper(BaseScraper):

    RSS_FEEDS = {
        "VentureBeat AI": "https://venturebeat.com/category/ai/feed/",
        "TechCrunch AI": "https://techcrunch.com/tag/artificial-intelligence/feed/",
        "MIT Tech Review AI": "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
        "DeepLearning.ai The Batch": "https://www.deeplearning.ai/the-batch/feed/",
    }

    HN_API = "https://hacker-news.firebaseio.com/v0"

    async def fetch_rss_news(self) -> list[dict]:
        records = []

        for source_name, feed_url in self.RSS_FEEDS.items():
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:50]:
                    record = {
                        "schemaVersion": "1.0",
                        "recordType": "NEWS",
                        "source": {"name": source_name, "url": entry.get("link")},
                        "content": {
                            "title": entry.get("title"),
                            "summary": entry.get("summary") or entry.get("description"),
                            "published_date": entry.get("published") or entry.get("updated"),
                            "source_name": source_name,
                        },
                        "collectedAt": datetime.utcnow().isoformat() + "Z",
                    }
                    records.append(record)
                logger.info(f"Fetched {len(feed.entries)} news items from {source_name}")
            except Exception as e:
                logger.error(f"Failed to parse RSS feed {source_name}: {e}")

        logger.info(f"Total RSS news records: {len(records)}")
        return records

    async def fetch_hn_ai_stories(self, limit: int = 100) -> list[dict]:
        import aiohttp

        async with aiohttp.ClientSession() as session:
            story_ids_url = f"{self.HN_API}/topstories.json"
            story_ids = await self.fetch_json(session, story_ids_url)

            if not story_ids:
                return []

            records = []
            for sid in story_ids[:limit]:
                item_url = f"{self.HN_API}/item/{sid}.json"
                item = await self.fetch_json(session, item_url)
                if item and item.get("type") == "story":
                    title = item.get("title", "")
                    if "ai" in title.lower() or "artificial" in title.lower() or "llm" in title.lower():
                        record = {
                            "schemaVersion": "1.0",
                            "recordType": "NEWS",
                            "source": {"name": "Hacker News", "url": item.get("url") or f"https://news.ycombinator.com/item?id={sid}"},
                            "content": {
                                "title": title,
                                "summary": item.get("text"),
                                "published_date": datetime.utcfromtimestamp(item.get("time", 0)).isoformat(),
                                "source_name": "Hacker News",
                            },
                            "collectedAt": datetime.utcnow().isoformat() + "Z",
                        }
                        records.append(record)
                await asyncio.sleep(0.1)

        logger.info(f"Fetched {len(records)} AI stories from HN")
        return records
