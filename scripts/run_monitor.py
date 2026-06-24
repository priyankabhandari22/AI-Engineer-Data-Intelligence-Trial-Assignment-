#!/usr/bin/env python3
"""Day 2: Monitor news + jobs (last 24 hours)."""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from loguru import logger
from src.scrapers.news_scraper import NewsScraper
from src.scrapers.job_scraper import JobScraper
from src.storage.database import init_structured_db, get_connection, insert_news, insert_job
from src.freshness.date_parser import parse_date, is_within_24_hours
import config.settings as settings


async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-all", action="store_true", help="Save all items regardless of freshness")
    args = parser.parse_args()

    logger.add(settings.LOG_PATH, rotation="10 MB")
    logger.info("=== MONITOR RUN STARTING ===")

    init_structured_db(settings.STRUCTURED_DB_PATH)
    conn = get_connection(settings.STRUCTURED_DB_PATH)

    # News
    logger.info("--- Fetching RSS news ---")
    news_scraper = NewsScraper(concurrency=5)
    news_items = await news_scraper.fetch_rss_news()

    fresh_news = []
    for item in news_items:
        pub_date = parse_date(item["content"].get("published_date"))
        is_fresh = is_within_24_hours(pub_date)
        if is_fresh or args.include_all:
            fresh_news.append(item)
            insert_news(conn, item)

    logger.info(f"News: {len(news_items)} total, {len(fresh_news)} saved")

    # Jobs
    logger.info("--- Fetching RemoteOK jobs ---")
    job_scraper = JobScraper(concurrency=5)
    jobs = await job_scraper.fetch_remoteok_jobs()

    fresh_jobs = []
    for job in jobs:
        pub_date = parse_date(job["content"].get("date"))
        is_fresh = is_within_24_hours(pub_date)
        if is_fresh or args.include_all:
            fresh_jobs.append(job)
            insert_job(conn, job)

    logger.info(f"Jobs: {len(jobs)} total, {len(fresh_jobs)} saved")

    conn.close()
    logger.info("=== MONITOR RUN COMPLETE ===")


if __name__ == "__main__":
    asyncio.run(main())
