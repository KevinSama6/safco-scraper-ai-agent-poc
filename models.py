from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ProductVariant(BaseModel):
    sku: Optional[str] = Field(
        None,
        description="The visible Stock Keeping Unit (SKU), item number, item code, product code, or catalog number for this variant if available"
    )
    size_or_color: Optional[str] = Field(
        None,
        description="Pack size, glove size, color, or volume variant if applicable"
    )
    price: Optional[float] = Field(
        None,
        description="Price of this variant as a float if publicly visible"
    )
    availability: Optional[str] = Field(
        None,
        description="Availability status such as in stock, out of stock, or backordered if visible"
    )


class ProductModel(BaseModel):
    product_name: str = Field(
        description="The full title of the product"
    )
    brand: Optional[str] = Field(
        None,
        description="Manufacturer or brand name if visible"
    )
    category_hierarchy: List[str] = Field(
        default_factory=list,
        description="Breadcrumb or category list from top to specific"
    )
    product_url: str = Field(
        description="The full URL of the product detail page"
    )
    description: Optional[str] = Field(
        None,
        description="Main product description or overview text"
    )
    specifications: Optional[Dict[str, Any]] = Field(
        None,
        description="Key-value pairs of technical attributes or specifications"
    )
    image_urls: List[str] = Field(
        default_factory=list,
        description="List of image URLs for the product"
    )
    alternative_products: List[str] = Field(
        default_factory=list,
        description="Names or URLs of suggested alternative products"
    )
    variants: List[ProductVariant] = Field(
        default_factory=list,
        description="List of product variations such as different sizes, packs, SKUs, prices, and availability values"
    )