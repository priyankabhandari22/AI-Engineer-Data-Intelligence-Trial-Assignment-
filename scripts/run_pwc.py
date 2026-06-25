#!/usr/bin/env python3
"""Fetch papers from PapersWithCode API."""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from loguru import logger
from src.scrapers.paper_scraper import PaperScraper
from src.storage.database import init_structured_db, get_connection, insert_paper
import config.settings as settings


async def main():
    logger.add(settings.LOG_PATH, rotation="10 MB")
    logger.info("=== PWC SCRAPE STARTING ===")

    init_structured_db(settings.STRUCTURED_DB_PATH)
    conn = get_connection(settings.STRUCTURED_DB_PATH)

    scraper = PaperScraper(concurrency=5)
    papers = await scraper.fetch_hf_daily_papers(limit=100)

    for p in papers:
        insert_paper(conn, p)
    logger.info(f"Saved {len(papers)} HuggingFace daily papers to database")

    conn.close()
    logger.info("=== PWC SCRAPE COMPLETE ===")


if __name__ == "__main__":
    asyncio.run(main())
