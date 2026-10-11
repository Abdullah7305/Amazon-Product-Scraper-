import asyncio
import os
import sys
from loguru import logger


from src.parser.product_parser import AmazonProductParser
from src.pipeline.amazon_pipeline import AmazonPipeline
from src.run import Engine

logger.remove()
logger.add(
    sys.stderr,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    ),
    level="INFO",
)

TARGET_URLS = [
    "https://www.amazon.com/MSI-Codex-Gaming-Desktop-A8NVP-436US/dp/B0F15TM77B/ref=sr_1_15?_encoding=UTF8&content-id=amzn1.sym.2ed5cb2d-6276-4908-8487-054be25673ca&dib=eyJ2IjoiMSJ9._JlFlMYMNq0x5kzlxp9l6TOGu2gPNu8sHTAW_gfRTChy5XUJ3vR274-S0Pu3y2niAtVuIQsybuq9miym8Vqyb6OR4mKKVYR7HJqx24jJchuqBf_1CxeUwKLeJuUow8kVfKIPxHRsEGqOe3QB-oGNidCXN6GnvmDjqicAtCbFuKG1XcrvORh2DKFt4vFj_13lj9av5jSTALuqvNmS_derMuxNz-UZ5y-lp4F77tU-1Vo.IN3DD6rQGN1c-rKEK1QFLPy-uT2Pf6bdtuv21Mmxsgg&dib_tag=se&keywords=desktop%2Bcomputers&pd_rd_r=24774345-8a23-4cdf-8ca1-c9fcea6db405&pd_rd_w=K6N0Q&pd_rd_wg=7oRd7&qid=1791670293&sr=8-15&th=1",
    "https://www.amazon.com/Under-Armour-Sleeve-T-Shirt-Heather/dp/B07D13B3N1/ref=sr_1_26?_encoding=UTF8&content-id=amzn1.sym.c9aac128-0f53-4ef3-9966-f21ec6e54087&dib=eyJ2IjoiMSJ9.Nx-7JeQ1pDUWY18td-3k8A-R-KM20dwU8ErVEfKihgJksdkBM5XKxeZbU1N5VnAfa3kms78bal0b2aW5zyq_z98FEJSbC17qvCshCH27YZKpbWo-zth9J8ovaSHWuSnFaEDih7Xh0RuEJPvnOewg0VivPRfRjJwBBOEk2ptqyJ_UgztwAIos4_YspHCjUoA95nMXN3z_fQV_xR_JLOa6lt2Hd5v23QCPS-8I0lGAkjgto4ZWuDKeWCsyjCSKGloiEQmE9hcLMunvh4Zagh47WRsJEy-AZTkms8Oi4phpyxA.Jix6HsgDDCh5eooksQQvf4NQGbFaax5z9CTod0rZqUo&dib_tag=se&keywords=fitness%2Bclothing&pd_rd_r=24774345-8a23-4cdf-8ca1-c9fcea6db405&pd_rd_w=5rP9R&pd_rd_wg=7oRd7&qid=1791670325&sr=8-26&th=1&psc=1",
    "https://www.amazon.com/Magicmode-Stainless-Precision-Gyroscope-Anti-Gravity/dp/B08GP72RFX/ref=sr_1_1?crid=3EAC2SG912JUG&dib=eyJ2IjoiMSJ9.aW0-zzTPDmalxh8a0HMyfllIgUHwAIhWct3KMkwXh0XCYKD7Iwc77S0Bu1PkbfySGewa0ybrTKKSoayHBEWHZEycjCU0wuIRzDaX-pY0uOEXz9Qlt0fL-ZFr5MuRcNz43L7RzVDp211bOcLmlKCFSDEx790-jLIyasFKIwTI6KPURl2l4s9sr4BujXCDoElzqWP274EkRme6pBX7Pq24gwL8PQ7PLiMdWZvE_TnrHzh8J6_DlaASmPmnmjGBZs5ymjg08bRMPciRVf6slTOWYg.DTg6Ch6iOrVqN25FKRg2H3yRaFuuHHD3d6vmegXVEmI&dib_tag=se&keywords=big%2Bbang%2Bpegasus&qid=1791670469&sprefix=big%2Bbang%2Bpe%2Caps%2C461&sr=8-1&th=1",
    "https://www.amazon.com/this-is-a-fake-broken-url-12345",
]


async def main():
    logger.info("[STARTING WORKFLOW] Initializing execution components...")

    os.makedirs("output", exist_ok=True)

    engine = Engine(product_urls=TARGET_URLS)
    parser = AmazonProductParser()
    pipeline = AmazonPipeline()

    try:

        await pipeline.open("output/products.jsonl")

        logger.info("[STREAMING STARTED] Fetching engine run loop active...")

        async for page in engine.run():
            try:

                item = parser.parse(html=page.html, url=page.url)

                await pipeline.process(item)

            except Exception as e:
                logger.exception(
                    f"[STREAM INTERRUPT] Failed to process a yielded page: {page.url} | Error: {e}"
                )

    except KeyboardInterrupt:
        logger.warning("[USER INTERRUPT] Process manually stopped.")
    except Exception as e:
        logger.critical(f"[CRITICAL FAILURE] Master run loop crashed: {e}")
    finally:

        await pipeline.close()
        logger.info("[WORKFLOW COMPLETE] Scraper shut down safely.")


if __name__ == "__main__":
    asyncio.run(main())
