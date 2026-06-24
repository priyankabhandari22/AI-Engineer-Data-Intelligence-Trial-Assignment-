import asyncio
import aiohttp
from datetime import datetime
from loguru import logger
from .base_scraper import BaseScraper
import config.settings as settings


class ProductScraper(BaseScraper):

    async def fetch_product_hunt_products(self, limit: int = 1000) -> list[dict]:
        if not settings.PRODUCT_HUNT_TOKEN:
            logger.warning("PRODUCT_HUNT_TOKEN not set, skipping Product Hunt")
            return []

        headers = {
            "Authorization": f"Bearer {settings.PRODUCT_HUNT_TOKEN}",
            "Content-Type": "application/json",
        }

        records = []
        cursor = None
        async with aiohttp.ClientSession() as session:
            while len(records) < limit:
                after_arg = f'after: "{cursor}"' if cursor else ""
                query = f"""
                {{
                  posts(first: 50, order: VOTES {after_arg}) {{
                    edges {{
                      node {{
                        name
                        tagline
                        website
                        url
                        description
                      }}
                    }}
                    pageInfo {{
                      endCursor
                      hasNextPage
                    }}
                  }}
                }}
                """

                resp = await session.post(
                    settings.PRODUCT_HUNT_API,
                    json={"query": query},
                    headers=headers,
                )

                if resp.status == 401:
                    logger.error("Product Hunt API: 401 Unauthorized — check your token")
                    break
                elif resp.status == 429:
                    wait = 120
                    logger.warning(f"Product Hunt rate limited, waiting {wait}s...")
                    await asyncio.sleep(wait)
                    continue
                elif resp.status != 200:
                    logger.warning(f"Product Hunt API error: {resp.status}")
                    break

                data = await resp.json()
                if data.get("errors"):
                    logger.warning(f"Product Hunt GraphQL errors: {data['errors']}")
                    break

                posts = data.get("data", {}).get("posts", {})
                edges = posts.get("edges", [])
                if not edges:
                    break

                for edge in edges:
                    node = edge["node"]
                    record = {
                        "schemaVersion": "1.0",
                        "recordType": "PRODUCT",
                        "source": {"name": "Product Hunt", "url": node.get("url")},
                        "content": {
                            "productName": node.get("name"),
                            "startupName": None,
                            "description": node.get("tagline") or node.get("description"),
                            "pricingModel": None,
                            "website": node.get("website"),
                            "category": None,
                        },
                        "collectedAt": datetime.utcnow().isoformat() + "Z",
                    }
                    records.append(record)
                    if len(records) >= limit:
                        break

                page_info = posts.get("pageInfo", {})
                cursor = page_info.get("endCursor")
                if not page_info.get("hasNextPage") or not cursor:
                    break

                await asyncio.sleep(1)

        logger.info(f"Fetched {len(records)} products from Product Hunt")
        return records
