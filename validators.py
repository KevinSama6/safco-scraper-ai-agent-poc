from models import ProductModel


def clean_sku(sku):
    
    # Clean invalid Stock Keeping Unit (SKU) values.
    # Some product pages may contain internal option values such as 0 or 1.
    # These values are not real SKUs, so they should not be exported as SKU values.
    
    if sku is None:
        return None

    sku = str(sku).strip()

    invalid_values = {
        "",
        "0",
        "1",
        "none",
        "null",
        "n/a",
        "na",
        "not available",
        "unknown",
    }

    if sku.lower() in invalid_values:
        return None

    return sku


def validate_and_clean_product(product: ProductModel) -> ProductModel:
   
    # Apply lightweight validation and cleanup to the extracted product.
    # Current validation:
    # - Removes obvious invalid SKU values.
    # - Keeps missing fields as None instead of forcing fake values.
   
    for variant in product.variants:
        variant.sku = clean_sku(variant.sku)

    return product