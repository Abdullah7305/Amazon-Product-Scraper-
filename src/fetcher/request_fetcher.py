from scrapling.fetchers import FetcherSession, ProxyRotator, AsyncStealthySession
from src.config.project_settings import config
from abc import ABC, abstractmethod
from loguru import logger
import asyncio


class Fetcher(ABC):
    @abstractmethod
    async def initlize_session(self, proxy=None):
        pass

    @abstractmethod
    async def close_session(self):
        pass

    @abstractmethod
    async def fetch(self, req_url: str):
        pass


class HTTTPFetcher(Fetcher):

    def __init__(self):
        self.session = None

    async def initlize_session(self, proxy=None):
        self.session = FetcherSession(
            impersonate="chrome124",
            stealthy_headers=True,  # Changed to True to inject browser headers automatically
            timeout=int(config.request_timeout),
            retries=int(config.max_retries),
            proxy=proxy,
        )
        self.session = await self.session.__aenter__()

    async def close_session(self):
        if self.session:
            await self.session.__aexit__(None, None, None)
            self.session = None

    async def fetch(self, req_url: str):
        try:
            # Explicit browser headers to blend in seamlessly with real traffic
            headers = {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Referer": "https://www.google.com/",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }

            response = await self.session.get(url=req_url, headers=headers)
            return response
        except Exception as e:
            logger.error(f"[Network Error]: {e}")
            return None


class StealthFetcher(Fetcher):

    def __init__(self):
        self.session = None

    async def initlize_session(self, proxy=None):
        self.session = AsyncStealthySession(
            headless=True,
            real_chrome=True,
            block_webrtc=True,
            solve_cloudflare=False,
            timeout=35000,
            proxy=proxy,
        )
        self.session = await self.session.__aenter__()

    async def close_session(self):
        if self.session:
            await self.session.__aexit__(None, None, None)
            self.session = None

    async def fetch(self, req_url: str):
        try:

            response = await self.session.fetch(url=req_url)
            return response
        except Exception as e:
            logger.error(f"[Network Error]: {e}")
            return None


class FetcherContext:
    def __init__(self, strategy: Fetcher):
        self.strategy = strategy

    async def initlize_session(self, proxy=None):
        await self.strategy.initlize_session(proxy=proxy)

    async def close_session(self):
        await self.strategy.close_session()

    async def fetch(self, req_url: str):
        return await self.strategy.fetch(req_url=req_url)


http_fetcher = FetcherContext(HTTTPFetcher())
stealth_fetcher = FetcherContext(StealthFetcher())


async def main():
    http_fetcher = FetcherContext(HTTTPFetcher())
    await http_fetcher.initlize_session(proxy=None)
    response = await http_fetcher.fetch("https://www.google.com/")
    print("Response: ", response)
    await http_fetcher.close_session()


if __name__ == "__main__":
    asyncio.run(main=main())
