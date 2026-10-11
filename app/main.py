import asyncio
from dataclasses import asdict
import sys
from typing import List, Tuple
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger

from app.schemas import ProductResponse, ScrapeRequest, ScrapeResponse
from src.items.items import FailedProductItem, ProductDetailItem
from src.parser.product_parser import AmazonProductParser
from src.run import Engine
from fastapi.middleware.cors import CORSMiddleware

# 1. Setup SlowAPI Rate Limiter
try:
    from slowapi import Limiter
    from slowapi.errors import RateLimitExceeded
    from slowapi.util import get_remote_address

    limiter = Limiter(key_func=get_remote_address)
    RATE_LIMIT_ENABLED = True
except ImportError:
    RATE_LIMIT_ENABLED = False
    logger.warning("[RATE LIMITER] slowapi not installed. Running without rate limits.")


# 2. Initialize FastAPI App
app = FastAPI(
    title="Amazon Product Scraper API",
    description="Send Amazon product URLs and get structured product data back.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],  # Allows requests from any frontend origin (or specify ["http://localhost:5173"])
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods including OPTIONS, GET, POST, etc.
    allow_headers=["*"],  # Allows all headers like Content-Type
)

if RATE_LIMIT_ENABLED:
    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={
                "error": "Too many requests. Please wait and try again.",
                "retry_after": "60 seconds",
            },
        )


# 3. Health Check Endpoints
@app.get("/")
async def root():
    return {
        "status": "running",
        "service": "Amazon Product Scraper API",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "engine": "ready", "parser": "ready"}


# 4. Background Scraper Engine Worker (Runs on a Proactor loop on Windows)
async def _async_scrape_task(
    urls: List[str],
) -> Tuple[List[ProductResponse], List[str]]:
    """Runs the Engine generator and parser inside an isolated event loop."""
    engine = Engine(product_urls=urls)
    parser = AmazonProductParser()

    products: List[ProductResponse] = []
    failed_urls: List[str] = []

    try:
        async for page in engine.run():
            try:
                item = parser.parse(html=page.html, url=page.url)

                if isinstance(item, ProductDetailItem):
                    product_data = asdict(item)
                    products.append(ProductResponse(**product_data))
                    logger.info(f"[API] Parsed successfully: {item.asin}")

                elif isinstance(item, FailedProductItem):
                    failed_urls.append(page.url)
                    logger.warning(f"[API] Parse failed: {page.url}")

            except Exception as e:
                failed_urls.append(page.url)
                logger.error(f"[API] Processing error for {page.url}: {e}")

    except Exception as e:
        logger.critical(f"[API] Engine crashed: {e}")

    return products, failed_urls


def _sync_worker(urls: List[str]) -> Tuple[List[ProductResponse], List[str]]:
    """Initializes a Windows Proactor loop on the worker thread."""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    return asyncio.run(_async_scrape_task(urls))


# 5. Main Scrape Endpoint
@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_products(
    request: Request,
    body: ScrapeRequest,
):
    """
    Accepts a list of Amazon product URLs, scrapes them,
    and returns structured product data.
    """
    urls = body.urls
    logger.info(f"[API] Received scrape request for {len(urls)} URL(s)")

    # Offload the scraper execution to a dedicated thread with its own ProactorEventLoop
    products, failed_urls = await asyncio.to_thread(_sync_worker, urls)

    response = ScrapeResponse(
        total_requested=len(urls),
        total_success=len(products),
        total_failed=len(failed_urls),
        products=products,
        failed_urls=failed_urls,
    )

    logger.info(
        f"[API] Request complete: {response.total_success} success, "
        f"{response.total_failed} failed"
    )

    return response


# {
#   "urls": [
#     "https://www.amazon.com/MSI-Codex-Gaming-Desktop-A8NVP-436US/dp/B0F15TM77B"
#   ]
# }
