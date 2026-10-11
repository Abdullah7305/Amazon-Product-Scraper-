import re
from dataclasses import asdict
from typing import List, Union

from loguru import logger

from src.items.items import FailedProductItem, ProductDetailItem
from src.database.postgres_db import postgres_db
from src.service.openai_llm import llm_service
from src.utils.file_storage import (
    SaveToJSON,
    StorageContext,
    csv_strategy,
    json_strategy,
)


class AmazonPipeline:
    """Handles deduplication, cleaning, AI enrichment, and persistence of items."""

    IMPORTANT_FIELDS = [
        "title",
        "price",
        "brand",
        "description",
        "rating",
        "bullet_points",
    ]

    PROTECTED_NUMERIC_FIELDS = {"price", "rating", "review_count"}

    def __init__(self):
        self.storage = StorageContext()
        self.llm = llm_service
        self.db = postgres_db
        self.seen_asins: set = set()
        self.failed_items: List[FailedProductItem] = []
        self.saved_count: int = 0
        self.skipped_count: int = 0
        logger.info("[PIPELINE INITIALIZED]")

    async def open(self, output_path: str) -> bool:
        """Selects a storage strategy based on file extension and opens the file."""
        if not output_path:
            raise ValueError("[PIPELINE] Output path cannot be empty.")

        lowered = output_path.lower()

        if lowered.endswith(".json") or lowered.endswith(".jsonl"):
            self.storage.set_strategy(json_strategy)
        elif lowered.endswith(".csv"):
            self.storage.set_strategy(csv_strategy)
        else:
            raise ValueError(
                f"[PIPELINE] Unsupported output format: '{output_path}'. "
                "Use a .json, .jsonl, or .csv extension."
            )

        opened = await self.storage.open_file(output_path)
        self.db.open()
        self.db.create_table()
        if not opened:
            raise ValueError(f"[PIPELINE] Failed to open output file: {output_path}")

        logger.info(f"[PIPELINE READY] Writing results to: {output_path}")
        return True

    async def close(self) -> None:
        """Closes the main output file and dumps any failed items separately."""
        await self.storage.close_file()
        self.db.close()
        if self.failed_items:
            await self._dump_failed_items("output/failed_products.json")

        logger.info(
            f"[PIPELINE CLOSED] Saved: {self.saved_count} | "
            f"Skipped (duplicates): {self.skipped_count} | "
            f"Failed: {len(self.failed_items)}"
        )

    async def _dump_failed_items(self, path: str) -> None:
        """Writes all collected failures to a dedicated JSON file."""
        failure_storage = StorageContext(SaveToJSON())

        try:
            opened = await failure_storage.open_file(path)
            if not opened:
                logger.error("[PIPELINE] Could not open failure dump file.")
                return

            for failed in self.failed_items:
                await failure_storage.save_data(asdict(failed))

            logger.warning(
                f"[PIPELINE] Wrote {len(self.failed_items)} failed items to {path}"
            )
        except Exception as e:
            logger.error(f"[PIPELINE] Failure dump error: {e}")
        finally:
            await failure_storage.close_file()

    async def process(self, item: Union[ProductDetailItem, FailedProductItem]) -> bool:
        """Processes a single parsed item through the full pipeline."""
        if item is None:
            logger.warning("[PIPELINE] Received a None item. Skipping.")
            return False

        if isinstance(item, FailedProductItem):
            await self._handle_failed(item)
            return False

        if not isinstance(item, ProductDetailItem):
            logger.error(f"[PIPELINE] Unknown item type: {type(item)}")
            return False

        if self._is_duplicate(item.asin):
            self.skipped_count += 1
            logger.info(f"[PIPELINE DUPLICATE] Skipping ASIN: {item.asin}")
            return False

        try:
            self._clean_item(item)

            missing_fields = self._get_missing_fields(item)

            if missing_fields:
                logger.info(
                    f"[PIPELINE MISSING] ASIN {item.asin} missing: {missing_fields}"
                )
                await self._ai_fill(item, missing_fields)
            else:
                logger.info(f"[PIPELINE COMPLETE] ASIN {item.asin} needs no AI help.")

            saved = await self.storage.save_data(asdict(item))
            self.db.save_data(asdict(item))
            record = self.db.get_data()
            print("Record: ", record)
            if saved:
                self.saved_count += 1
                logger.success(
                    f"[PIPELINE SAVED] ASIN: {item.asin} | {item.title[:60]}"
                )
                return True

            logger.error(f"[PIPELINE SAVE FAILED] ASIN: {item.asin}")
            self._record_failure(
                url=item.product_url,
                asin=item.asin,
                failure_type="STORAGE_ERROR",
                message="Storage layer returned False while saving item.",
            )
            return False

        except Exception as e:
            logger.exception(f"[PIPELINE ERROR] ASIN: {item.asin} | {e}")
            self._record_failure(
                url=item.product_url,
                asin=item.asin,
                failure_type="PIPELINE_ERROR",
                message=str(e),
            )
            return False

    async def _handle_failed(self, item: FailedProductItem) -> None:
        """Collects a parser-level failure for the error dump."""
        logger.warning(
            f"[PIPELINE FAILED ITEM] URL: {item.url} | "
            f"Type: {item.failure_type} | Reason: {item.failure_message}"
        )
        self.failed_items.append(item)

    def _record_failure(
        self, url: str, asin: str, failure_type: str, message: str
    ) -> None:
        """Builds and stores a FailedProductItem from a runtime pipeline error."""
        from datetime import datetime

        self.failed_items.append(
            FailedProductItem(
                url=url,
                asin=asin,
                timestamp=datetime.utcnow().isoformat(),
                failure_type=failure_type,
                failure_message=message,
                retry_count=0,
            )
        )

    def _is_duplicate(self, asin: str) -> bool:
        """Returns True if the ASIN was already processed in this run."""
        if not asin or asin == "UNKNOWN":

            return False

        if asin in self.seen_asins:
            return True

        self.seen_asins.add(asin)
        return False

    def _clean_item(self, item: ProductDetailItem) -> None:
        """Normalizes all fields in place. Synchronous: pure CPU work."""

        if item.title:
            item.title = " ".join(item.title.split())

        if item.brand:
            item.brand = " ".join(item.brand.split()).strip(" ,-|")
            if not item.brand:
                item.brand = None

        if item.seller:
            item.seller = " ".join(item.seller.split())
            if not item.seller:
                item.seller = None

        if item.description:
            cleaned = re.sub(r"\s+", " ", item.description).strip()
            item.description = cleaned if cleaned else None

        if item.availability:
            availability = " ".join(item.availability.split())
            item.availability = availability.title() if availability else None

        if item.bullet_points:
            item.bullet_points = [
                " ".join(bullet.split())
                for bullet in item.bullet_points
                if bullet and bullet.strip()
            ]

        if item.specifications:
            item.specifications = {
                " ".join(str(key).split()).strip(": "): " ".join(str(value).split())
                for key, value in item.specifications.items()
                if key and value and str(value).strip()
            }

        if item.images:
            unique_images = []
            for img in item.images:
                if img and img not in unique_images:
                    unique_images.append(img.strip())
            item.images = unique_images

        item.price = self._coerce_price(item.price)

        item.rating = self._coerce_rating(item.rating)

        item.review_count = self._coerce_review_count(item.review_count)

        if not item.currency:
            item.currency = "$"

    @staticmethod
    def _coerce_price(value) -> Union[float, None]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value) if value >= 0 else None
        try:
            cleaned = re.sub(r"[^\d.]", "", str(value))
            return float(cleaned) if cleaned else None
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _coerce_rating(value) -> Union[float, None]:
        if value is None:
            return None
        try:
            rating = float(value)
        except (ValueError, TypeError):
            return None
        return rating if 0.0 <= rating <= 5.0 else None

    @staticmethod
    def _coerce_review_count(value) -> Union[int, None]:
        if value is None:
            return None
        try:
            count = int(re.sub(r"\D", "", str(value)))
        except (ValueError, TypeError):
            return None
        return count if count >= 0 else None

    def _get_missing_fields(self, item: ProductDetailItem) -> List[str]:
        """Returns the list of important fields that are empty or None."""
        missing = []

        for field_name in self.IMPORTANT_FIELDS:
            value = getattr(item, field_name, None)

            if value is None:
                missing.append(field_name)
            elif isinstance(value, str) and not value.strip():
                missing.append(field_name)
            elif isinstance(value, (list, dict)) and len(value) == 0:
                missing.append(field_name)

        return missing

    async def _ai_fill(
        self, item: ProductDetailItem, missing_fields: List[str]
    ) -> None:
        """Calls the LLM to fill missing text fields. Never touches numeric fields."""

        fillable = [f for f in missing_fields if f not in self.PROTECTED_NUMERIC_FIELDS]
        if not fillable:
            logger.info(
                f"[AI SKIPPED] ASIN {item.asin}: only numeric fields missing "
                f"({missing_fields}). AI is not allowed to invent these."
            )
            return

        try:
            item_dict = asdict(item)
            results = await self.llm.process_and_validate_batch([item_dict])

            if not results or not isinstance(results, list):
                logger.warning(f"[AI NO RESPONSE] ASIN: {item.asin}")
                return

            ai_data = results[0]
            if not isinstance(ai_data, dict):
                logger.warning(f"[AI BAD FORMAT] ASIN: {item.asin}")
                return

            filled = []

            if "title" in fillable:
                clean_title = ai_data.get("clean_title")
                if clean_title and str(clean_title).strip():
                    item.title = str(clean_title).strip()
                    filled.append("title")

            if "brand" in fillable:
                ai_brand = ai_data.get("brand")
                if ai_brand and str(ai_brand).strip():
                    item.brand = str(ai_brand).strip()
                    filled.append("brand")

            if "description" in fillable:
                notes = ai_data.get("validation_notes") or ai_data.get("description")
                features = ai_data.get("key_features")
                if features and isinstance(features, list):
                    item.description = " ".join(str(f).strip() for f in features)
                    filled.append("description")
                elif notes and str(notes).strip():
                    item.description = str(notes).strip()
                    filled.append("description")

            if "bullet_points" in fillable:
                features = ai_data.get("key_features")
                if features and isinstance(features, list) and not item.bullet_points:
                    item.bullet_points = [
                        str(f).strip() for f in features if str(f).strip()
                    ]
                    filled.append("bullet_points")

            category = ai_data.get("category")
            if category and str(category).strip():
                if item.specifications is None:
                    item.specifications = {}
                item.specifications.setdefault("Category", str(category).strip())

            if filled:
                logger.info(f"[AI FILLED] ASIN {item.asin} -> fields: {filled}")
            else:
                logger.info(f"[AI NO FILL] ASIN {item.asin}: nothing usable returned.")

        except Exception as e:

            logger.error(f"[AI ERROR] ASIN {item.asin} | {e}")
