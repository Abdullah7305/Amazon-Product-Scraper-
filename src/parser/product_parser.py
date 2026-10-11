from datetime import datetime
import json
import re
from typing import Dict, List, Optional, Union
from bs4 import BeautifulSoup
from loguru import logger
from src.items.items import FailedProductItem, ProductDetailItem


class AmazonProductParser:

    def __init__(self):
        # Compiled regex for efficiency
        self.asin_pattern = re.compile(r"/(?:dp|gp/product)/([A-Z0-9]{10})")
        self.rating_pattern = re.compile(r"([0-9.]+)\s*(?:out of|de)\s*5")
        self.digits_only_pattern = re.compile(r"\D")

    def parse(self, html: str, url: str) -> Union[ProductDetailItem, FailedProductItem]:
        """Parses the raw HTML of an Amazon product page.

        Returns a ProductDetailItem on success, or a FailedProductItem if critical
        structural elements (like ASIN or Title) are missing.
        """
        soup = BeautifulSoup(html, "lxml")

        asin = self._extract_asin(url, soup)
        title = self._extract_title(soup)

        # CRITICAL FAIL CHECK: If we cannot find an ASIN or Title, it's a parsing failure
        if not title or asin == "UNKNOWN":
            failure_msg = []
            if not title:
                failure_msg.append("Product Title is empty or missing")
            if asin == "UNKNOWN":
                failure_msg.append("Could not extract ASIN from URL or HTML")

            logger.warning(f"[PARSING FAILED] {url} | Reason: {', '.join(failure_msg)}")

            return FailedProductItem(
                url=url,
                asin=asin if asin != "UNKNOWN" else None,
                timestamp=datetime.utcnow().isoformat(),
                failure_type="PARSING_ERROR",
                failure_message="; ".join(failure_msg),
                retry_count=0,  # Can be augmented by the manager if retry states exist
            )

        # Parse secondary fields
        brand = self._extract_brand(soup)
        price, currency = self._extract_price(soup)
        availability = self._extract_availability(soup)
        description = self._extract_description(soup)
        bullet_points = self._extract_bullet_points(soup)
        specifications = self._extract_specifications(soup)
        images = self._extract_images(soup)
        rating = self._extract_rating(soup)
        review_count = self._extract_review_count(soup)
        seller = self._extract_seller(soup)

        return ProductDetailItem(
            asin=asin,
            product_url=url,
            title=title,
            brand=brand,
            seller=seller,
            price=price,
            currency=currency,
            availability=availability,
            description=description,
            bullet_points=bullet_points,
            specifications=specifications,
            images=images,
            rating=rating,
            review_count=review_count,
        )

    def _extract_asin(self, url: str, soup: BeautifulSoup) -> str:
        # 1. Try extracting from URL (fastest & most reliable)
        match = self.asin_pattern.search(url)
        if match:
            return match.group(1)

        # 2. Fallback to scraping input fields inside page forms
        asin_input = soup.select_one(
            "input#ASIN, input[name='ASIN'], input[name='itemID']"
        )
        if asin_input and asin_input.get("value"):
            return asin_input["value"].strip()

        return "UNKNOWN"

    def _extract_title(self, soup: BeautifulSoup) -> str:
        title_tag = soup.select_one("#productTitle")
        if title_tag:
            return title_tag.get_text(strip=True)
        return ""

    def _extract_brand(self, soup: BeautifulSoup) -> str:
        brand_selectors = [
            "#bylineInfo",
            "#brand",
            "a#bylineInfo",
            "hr + div a.a-link-normal",
        ]
        for selector in brand_selectors:
            tag = soup.select_one(selector)
            if tag:
                text = tag.get_text(strip=True)
                # Clean up generic brand prefix strings
                for prefix in [
                    "Brand:",
                    "Visit the",
                    "Store",
                    "Brand Store",
                ]:
                    text = text.replace(prefix, "")
                return text.strip()
        return None

    def _extract_seller(self, soup: BeautifulSoup) -> Optional[str]:
        seller_selectors = [
            "#merchant-info a",
            "[data-action='show-all-offers-display'] a",
            "#sellerProfileTriggerId",
            "span.tabular-buybox-text-message a",
        ]
        for selector in seller_selectors:
            tag = soup.select_one(selector)
            if tag:
                return tag.get_text(strip=True)
        return None

    def _extract_price(self, soup: BeautifulSoup) -> tuple[Optional[float], str]:
        price_selectors = [
            ".a-price .a-offscreen",
            "#price_inside_buybox",
            "#priceblock_ourprice",
            "#priceblock_dealprice",
            "span.a-price span.a-offscreen",
        ]

        for selector in price_selectors:
            tag = soup.select_one(selector)
            if tag:
                raw_price = tag.get_text(strip=True)
                if raw_price:
                    # Capture currency symbol
                    currency = (
                        raw_price[0] if raw_price[0] in ["$", "£", "€", "¥"] else "$"
                    )
                    # Clean and parse numeric digits
                    clean_price = re.sub(r"[^\d.]", "", raw_price)
                    try:
                        return float(clean_price), currency
                    except ValueError:
                        continue
        return None, "$"

    def _extract_availability(self, soup: BeautifulSoup) -> Optional[str]:
        availability_tag = soup.select_one("#availability span")
        if availability_tag:
            return availability_tag.get_text(strip=True)
        return None

    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        desc_tag = soup.select_one("#productDescription p, #productDescription")
        if desc_tag:
            return desc_tag.get_text(strip=True)
        return None

    def _extract_bullet_points(self, soup: BeautifulSoup) -> List[str]:
        bullets = []
        items = soup.select("#feature-bullets ul li span.a-list-item")
        for item in items:
            text = item.get_text(strip=True)
            if text and "Make sure this fits" not in text:
                bullets.append(text)
        return bullets

    def _extract_specifications(self, soup: BeautifulSoup) -> Dict[str, str]:
        specs = {}
        # Try finding standard technical spec table (e.g., Electronics)
        table_rows = soup.select(
            "#productDetails_techSpec_section_1 tr, #technicalSpecifications_section_1 tr"
        )
        for row in table_rows:
            th = row.select_one("th")
            td = row.select_one("td")
            if th and td:
                key = th.get_text(strip=True)
                val = td.get_text(strip=True).replace(
                    "\u200e", ""
                )  # Clean clean-up chars
                specs[key] = val

        # Try alternative spec list design (e.g., Home Goods, Books)
        if not specs:
            detail_items = soup.select("#detailBullets_feature_div ul li")
            for li in detail_items:
                spans = li.select("span span")
                if len(spans) >= 2:
                    key = (
                        spans[0].get_text(strip=True).replace(":", "").replace("\n", "")
                    )
                    val = spans[1].get_text(strip=True)
                    specs[key] = val

        return specs

    def _extract_images(self, soup: BeautifulSoup) -> List[str]:
        images = []

        # 1. Look inside the dynamic image map JSON (best way to grab high-resolution source links)
        img_tag = soup.select_one("#landingImage, #imgBlkFront")
        if img_tag and img_tag.get("data-a-dynamic-image"):
            try:
                img_data = json.loads(img_tag["data-a-dynamic-image"])
                return list(img_data.keys())
            except json.JSONDecodeError:
                pass

        # 2. Fallback to alternative thumbnail elements
        thumb_tags = soup.select("#altImages img, #imageBlock img")
        for img in thumb_tags:
            src = img.get("src")
            if src:
                # Normalise image link to highest resolution variant
                hi_res_url = re.sub(r"\._AC_.*_\.", ".", src)
                if hi_res_url not in images:
                    images.append(hi_res_url)

        return images

    def _extract_rating(self, soup: BeautifulSoup) -> Optional[float]:
        rating_selectors = [
            "#acrPopover .a-icon-alt",
            "span.a-icon-alt",
            "i.a-icon-star .a-icon-alt",
        ]
        for selector in rating_selectors:
            tag = soup.select_one(selector)
            if tag:
                text = tag.get_text(strip=True)
                match = self.rating_pattern.search(text)
                if match:
                    try:
                        return float(match.group(1))
                    except ValueError:
                        continue
        return None

    def _extract_review_count(self, soup: BeautifulSoup) -> Optional[int]:
        review_selectors = [
            "#acrCustomerReviewText",
            "#acrCustomerReviewLink",
            "span[data-hook='total-review-count']",
        ]
        for selector in review_selectors:
            tag = soup.select_one(selector)
            if tag:
                text = tag.get_text(strip=True)
                # Strip spaces, commas, ratings label
                clean_text = self.digits_only_pattern.sub("", text)
                if clean_text:
                    try:
                        return int(clean_text)
                    except ValueError:
                        continue
        return None
