import asyncio
from dataclasses import dataclass
from typing import AsyncGenerator, Optional
from loguru import logger
from src.config.project_settings import config
from src.fetcher.request_fetcher import http_fetcher, stealth_fetcher
from src.reliability.antibot_detection import AntiBotDetector
from src.reliability.proxy_manager import proxy_manager
from src.reliability.trace_down_request import cooldown_queue_tracker


@dataclass
class FetchedPage:
    url: str
    html: str


class Engine:

    def __init__(self, product_urls: list[str]):
        self.fetcher = None
        self.tracer = cooldown_queue_tracker
        self.product_urls = product_urls
        self.is_session = False
        self.current_proxy = None
        self.proxy_manager = proxy_manager
        logger.info("[ENGINE INITIALIZED]")

    async def _initialize_session(self, fetcher=None):
        if self.is_session:
            return

        if fetcher is None:
            fetcher = http_fetcher

        self.current_proxy = self.proxy_manager.get_proxy()
        self.fetcher = fetcher

        try:
            await self.fetcher.initlize_session(proxy=self.current_proxy)
            self.is_session = True
            logger.info(
                f"[SESSION INITIALIZED] Proxy: {self.current_proxy} | Fetcher: {fetcher.__class__.__name__}"
            )
        except Exception as e:
            logger.error(f"[SESSION INITIALIZE FAILED] {e}")
            self.fetcher = None
            self.is_session = False
            raise

    async def _close_session(self):
        if not self.is_session or self.fetcher is None:
            return

        try:
            await self.fetcher.close_session()
        except Exception as e:
            logger.error(f"[SESSION CLOSE ERROR] {e}")
        finally:
            self.is_session = False
            self.fetcher = None
            logger.info("[SESSION CLOSED]")

    def save_error_file(self, err_msg):
        try:
            with open("error.log", "a", encoding="utf-8") as file:
                file.write(f"{err_msg}\n")
        except OSError:
            logger.error("[ERROR LOG WRITE FAILED]")

    async def _process_stealth_browser(self, url) -> Optional[str]:
        """Runs the stealth fallback request exactly once.

        Returns the HTML string on success, or None on failure.
        """
        logger.info(f"[STEALTH FALLBACK RUNNING] URL: {url}")
        await self._close_session()

        try:
            await self._initialize_session(stealth_fetcher)
            response = await self.fetcher.fetch(url)

            status = getattr(response, "status", None)
            html = getattr(response, "html_content", None)

            if not html or AntiBotDetector.is_blocked(html, status_code=status):
                logger.warning(f"[STEALTH BLOCKED/FAILED] URL: {url}")
                return None

            logger.info(f"[STEALTH SUCCESS] {url}")
            return html

        except Exception as e:
            logger.error(f"[STEALTH ERROR] URL: {url} | Error: {e}")
            return None
        finally:
            await self._close_session()

    async def _process_url(self, url: str) -> AsyncGenerator[FetchedPage, None]:
        """Processes a single URL, handling retries, cooldowns, and fallbacks.

        Yields a FetchedPage on success, then terminates execution for that URL.
        """
        while True:
            if self.tracer.is_exhausted(url):
                logger.error(f"[URL EXHAUSTED] Skipping permanently: {url}")
                return

            if not self.tracer.can_retry_now(url):
                wait_time = self.tracer.get_remaining_cooldown(url)
                logger.info(f"[COOLDOWN] Waiting {wait_time:.2f}s for: {url}")
                await asyncio.sleep(wait_time)

            if not self.is_session:
                try:
                    await self._initialize_session()
                except Exception:
                    self.tracer.register_failure(url, "Session initialization failed")
                    continue

            try:
                response = await self.fetcher.fetch(url)
                status = getattr(response, "status", None)
                html = getattr(response, "html_content", None)

                is_blocked = (
                    AntiBotDetector.is_blocked(html, status_code=status)
                    if html
                    else True
                )

                if is_blocked:
                    logger.warning(
                        f"[HTTP BLOCKED / INVALID] Code: {status} | URL: {url}. Trying Stealth Browser..."
                    )

                    stealth_html = await self._process_stealth_browser(url)

                    if stealth_html:
                        self.tracer.mark_success(url)
                        if self.current_proxy:
                            self.proxy_manager.report_success(self.current_proxy)
                        yield FetchedPage(url=url, html=stealth_html)
                        return
                    else:
                        self.tracer.mark_terminal_failure(
                            url,
                            reason="HTTP blocked and Stealth fallback failed",
                        )
                        self.save_error_file(
                            f"URL: {url} | Reason: Both HTTP & Stealth failed"
                        )
                        return

                self.tracer.mark_success(url)
                if self.current_proxy:
                    self.proxy_manager.report_success(self.current_proxy)
                logger.info(f"[SUCCESS] {url}")
                yield FetchedPage(url=url, html=html)
                return

            except Exception as e:
                logger.warning(f"[NETWORK/EXCEPTION] {url} | Error: {e}")

                if self.current_proxy:
                    self.proxy_manager.report_failure(self.current_proxy)

                await self._close_session()

                should_retry = self.tracer.register_failure(url, reason=str(e))
                if not should_retry:
                    self.save_error_file(f"URL: {url} | Reason: {e}")
                    return
                continue

    async def run(self) -> AsyncGenerator[FetchedPage, None]:
        """Loops over all target URLs and yields successfully fetched pages.

        Ensures active sessions are cleaned up cleanly upon completion or failure.
        """
        try:
            for url in self.product_urls:
                async for page in self._process_url(url):
                    yield page
        finally:
            await self._close_session()
