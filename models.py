from typing import List, Optional
from pydantic import BaseModel, Field


class ProductVariant(BaseModel):
    sku: str = Field(description="The unique item code or SKU for this variant")
    size_or_color: Optional[str] = Field(
        None,
        description="Pack size, glove size, or volume variant if applicable"
    )
    price: Optional[float] = Field(
        None,
        description="Price of this variant as a float"
    )
    availability: Optional[str] = Field(
        None,
        description="In stock, out of stock, or backordered status"
    )


class ProductModel(BaseModel):
    product_name: str = Field(description="The full title of the product")
    brand: Optional[str] = Field(None, description="Manufacturer or brand name")
    category_hierarchy: List[str] = Field(
        default=[],
        description="Breadcrumb or category list from top to specific"
    )
    product_url: str = Field(description="The full URL of the product detail page")
    description: Optional[str] = Field(
        None,
        description="Main product description or overview text"
    )
    specifications: Optional[dict] = Field(
        None,
        description="Key-value pairs of technical attributes or specs"
    )
    image_urls: List[str] = Field(
        default=[],
        description="List of image URLs for the product"
    )
    alternative_products: List[str] = Field(
        default=[],
        description="Names or URLs of suggested alternative products"
    )
    variants: List[ProductVariant] = Field(
        default=[],
        description="List of product variations under this product"
    )