import asyncio
import aiohttp
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from fake_useragent import UserAgent


class BaseScraper:
    def __init__(self, concurrency: int = 10, timeout: int = 30):
        self.concurrency = concurrency
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.ua = UserAgent()
        self.semaphore = asyncio.Semaphore(concurrency)
        self._playwright_browser = None

    def get_headers(self) -> dict:
        return {
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

    async def _ensure_browser(self):
        if self._playwright_browser is None:
            from playwright.async_api import async_playwright
            p = await async_playwright().start()
            self._playwright_browser = await p.chromium.launch(headless=True)
        return self._playwright_browser

    async def _fetch_with_playwright(self, url: str) -> str | None:
        try:
            browser = await self._ensure_browser()
            context = await browser.new_context(
                user_agent=self.ua.random,
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
            )
            page = await context.new_page()
            await page.goto(url, wait_until="networkidle", timeout=30000)
            content = await page.content()
            await context.close()
            return content
        except Exception as e:
            logger.warning(f"Playwright fallback failed for {url}: {e}")
            return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def fetch(self, session: aiohttp.ClientSession, url: str, use_playwright_fallback: bool = True) -> str | None:
        async with self.semaphore:
            try:
                async with session.get(url, headers=self.get_headers(), timeout=self.timeout) as resp:
                    if resp.status == 200:
                        return await resp.text()
                    elif resp.status == 429:
                        logger.warning(f"Rate limited on {url}, backing off...")
                        await asyncio.sleep(60)
                        raise Exception("Rate limited")
                    elif resp.status == 403 and use_playwright_fallback:
                        logger.info(f"Blocked (403) on {url}, trying Playwright fallback...")
                        return await self._fetch_with_playwright(url)
                    elif resp.status == 404:
                        logger.info(f"Not found: {url}")
                        return None
                    else:
                        logger.warning(f"Status {resp.status} for {url}")
                        return None
            except asyncio.TimeoutError:
                logger.error(f"Timeout on {url}")
                return None

    async def fetch_json(self, session: aiohttp.ClientSession, url: str) -> dict | list | None:
        async with self.semaphore:
            try:
                async with session.get(url, headers=self.get_headers(), timeout=self.timeout) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    elif resp.status == 429:
                        logger.warning(f"Rate limited on {url}, backing off...")
                        await asyncio.sleep(60)
                        raise Exception("Rate limited")
                    else:
                        logger.warning(f"Status {resp.status} for {url}")
                        return None
            except asyncio.TimeoutError:
                logger.error(f"Timeout on {url}")
                return None

    async def fetch_many(self, urls: list[str]) -> list[tuple[str, str | None]]:
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch(session, url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        return list(zip(urls, results))
