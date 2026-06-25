#!/usr/bin/env python3
"""Scrape jobs from all job boards: RemoteOK, Greenhouse, Lever, Wellfound."""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from loguru import logger
from src.scrapers.job_scraper import JobScraper
from src.storage.database import init_structured_db, get_connection, insert_job
import config.settings as settings


async def main():
    logger.add(settings.LOG_PATH, rotation="10 MB")
    logger.info("=== JOB SCRAPE STARTING ===")

    init_structured_db(settings.STRUCTURED_DB_PATH)
    conn = get_connection(settings.STRUCTURED_DB_PATH)

    scraper = JobScraper(concurrency=5)

    # 1. RemoteOK
    remoteok = await scraper.fetch_remoteok_jobs()
    for j in remoteok:
        insert_job(conn, j)
    logger.info(f"RemoteOK: {len(remoteok)} saved")

    # 2. Greenhouse (multi-board)
    greenhouse = await scraper.fetch_all_greenhouse_jobs()
    for j in greenhouse:
        insert_job(conn, j)
    logger.info(f"Greenhouse: {len(greenhouse)} saved")

    # 3. Lever
    lever = await scraper.fetch_all_lever_jobs()
    for j in lever:
        insert_job(conn, j)
    logger.info(f"Lever: {len(lever)} saved")

    # 4. Extra Greenhouse boards
    extra_greenhouse = await scraper.fetch_more_greenhouse_boards()
    for j in extra_greenhouse:
        insert_job(conn, j)
    logger.info(f"Extra Greenhouse: {len(extra_greenhouse)} saved")

    total = len(remoteok) + len(greenhouse) + len(lever) + len(extra_greenhouse)
    conn.close()
    logger.info(f"=== JOB SCRAPE COMPLETE: {total} total ===")


if __name__ == "__main__":
    asyncio.run(main())
