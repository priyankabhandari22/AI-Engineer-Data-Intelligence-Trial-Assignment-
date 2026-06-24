import asyncio
import aiohttp
import os
from loguru import logger
import config.settings as settings


async def fetch_github_stars(session: aiohttp.ClientSession, repo_url: str) -> int | None:
    if not repo_url or "github.com" not in repo_url:
        return None

    parts = repo_url.rstrip("/").split("github.com/")
    if len(parts) < 2:
        return None

    owner_repo = parts[1].strip("/")
    api_url = f"{settings.GITHUB_API}/{owner_repo}"

    headers = {"Authorization": f"token {settings.GITHUB_TOKEN}"} if settings.GITHUB_TOKEN else {}

    try:
        async with session.get(api_url, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("stargazers_count")
    except Exception as e:
        logger.warning(f"GitHub stars fetch failed for {repo_url}: {e}")

    return None


async def enrich_papers_with_github_stars(papers: list[dict]) -> list[dict]:
    async with aiohttp.ClientSession() as session:
        for paper in papers:
            gh_url = paper["content"].get("github_url")
            if gh_url:
                stars = await fetch_github_stars(session, gh_url)
                paper["content"]["github_stars"] = stars
                logger.info(f"Stars for {gh_url}: {stars}")
            await asyncio.sleep(0.2)
    return papers
