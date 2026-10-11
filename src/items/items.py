from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class SearchProductItem:
    asin: str
    title: str
    product_url: str
    price: Optional[float] = None
    currency: Optional[str] = "$"
    rating: Optional[float] = None
    review_count: Optional[int] = None
    availability: Optional[str] = "In Stock"
    image_url: Optional[str] = None


@dataclass
class ProductDetailItem:
    asin: str
    product_url: str
    title: str
    brand: Optional[str] = None
    seller: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = "$"
    availability: Optional[str] = None
    description: Optional[str] = None
    bullet_points: List[str] = field(default_factory=list)
    specifications: Dict[str, str] = field(default_factory=dict)
    images: List[str] = field(default_factory=list)
    rating: Optional[float] = None
    review_count: Optional[int] = None


@dataclass
class FailedProductItem:
    url: str
    asin: Optional[str] = None
    timestamp: str = ""
    failure_type: str = ""
    failure_message: str = ""
    retry_count: int = 0
