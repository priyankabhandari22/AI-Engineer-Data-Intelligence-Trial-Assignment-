#!/usr/bin/env python3
"""Day 1-2: Bulk scrape all sources."""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from loguru import logger
from src.scrapers.paper_scraper import PaperScraper
from src.scrapers.startup_scraper import StartupScraper
from src.scrapers.product_scraper import ProductScraper
from src.scrapers.github_enricher import enrich_papers_with_github_stars
from src.storage.database import init_structured_db, get_connection, insert_startup, insert_product, insert_paper
import config.settings as settings


async def main():
    logger.add(settings.LOG_PATH, rotation="10 MB")
    logger.info("=== BULK SCRAPE STARTING ===")

    init_structured_db(settings.STRUCTURED_DB_PATH)
    conn = get_connection(settings.STRUCTURED_DB_PATH)

    # 1. Research Papers
    logger.info("--- Fetching ArXiv papers ---")
    paper_scraper = PaperScraper(concurrency=5)
    papers = await paper_scraper.fetch_arxiv_papers(max_results=1000)
    logger.info(f"Got {len(papers)} papers from ArXiv")

    logger.info("--- Enriching with GitHub stars ---")
    papers = await enrich_papers_with_github_stars(papers)
    logger.info(f"GitHub enrichment complete for {len(papers)} papers")

    for p in papers:
        insert_paper(conn, p)
    logger.info(f"Saved {len(papers)} papers to database")

    # 2. Startups
    logger.info("--- Fetching YC startups ---")
    startup_scraper = StartupScraper(concurrency=5)
    startups = await startup_scraper.fetch_yc_startups()
    logger.info(f"Got {len(startups)} startups from YC")

    for s in startups:
        insert_startup(conn, s)
    logger.info(f"Saved {len(startups)} startups to database")

    # 3. Products
    logger.info("--- Fetching Product Hunt products ---")
    product_scraper = ProductScraper(concurrency=5)
    if settings.PRODUCT_HUNT_TOKEN:
        products = await product_scraper.fetch_product_hunt_products(limit=1000)
        logger.info(f"Got {len(products)} products from Product Hunt")
    else:
        logger.warning("PRODUCT_HUNT_TOKEN not set, skipping Product Hunt")
        products = []

    for p in products:
        insert_product(conn, p)
    logger.info(f"Saved {len(products)} products to database")

    conn.close()
    logger.info("=== BULK SCRAPE COMPLETE ===")
    logger.info(f"Papers: {len(papers)}, Startups: {len(startups)}, Products: {len(products)}")


if __name__ == "__main__":
    asyncio.run(main())
