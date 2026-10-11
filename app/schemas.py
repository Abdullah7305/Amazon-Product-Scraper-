from typing import Dict, List, Optional
from pydantic import BaseModel, Field


# ---- REQUEST: What the user sends to us ----
class ScrapeRequest(BaseModel):
    urls: List[str] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="List of Amazon product URLs to scrape (max 10 per request)",
    )


# ---- RESPONSE: What we send back to the user ----
class ProductResponse(BaseModel):
    asin: str
    title: str
    brand: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = "$"
    rating: Optional[float] = None
    review_count: Optional[int] = None
    availability: Optional[str] = None
    description: Optional[str] = None
    bullet_points: List[str] = []
    specifications: Dict[str, str] = {}
    images: List[str] = []
    product_url: str


class ScrapeResponse(BaseModel):
    total_requested: int
    total_success: int
    total_failed: int
    products: List[ProductResponse] = []
    failed_urls: List[str] = []