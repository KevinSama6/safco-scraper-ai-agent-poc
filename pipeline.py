import time

from db import (
    init_db,
    insert_url,
    get_next_pending_url,
    update_url_status,
    save_product,
)
from scraper import fetch_page_with_retry
from agents import (
    classify_page_type,
    run_navigator_agent,
    run_extractor_agent,
)
from validators import validate_and_clean_product


SEED_CATEGORIES = [
    "https://www.safcodental.com/catalog/sutures-surgical-products",
    "https://www.safcodental.com/catalog/gloves",
]

MAX_POC_PRODUCTS = 5
REQUEST_DELAY_SECONDS = 2


def bootstrap_system() -> None:
   
    # Initialize the database and insert seed category URLs.
    
    init_db()

    for url in SEED_CATEGORIES:
        insert_url(url, "category")

    print("[Pipeline] System bootstrapped with seed categories.")


def discover_product_urls_from_categories() -> None:
    
    # Phase A:
    # Process pending category URLs, extract product detail URLs,
    # and insert discovered product URLs into urls_queue as product tasks.
    
    print("\n--- [Phase A] Discovering Product URLs from Categories ---")

    while True:
        cat_url = get_next_pending_url("category")

        if not cat_url:
            print("[Pipeline] No more pending categories.")
            break

        print(f"\n[Pipeline] Processing category: {cat_url}")

        try:
            html = fetch_page_with_retry(cat_url)

            page_type = classify_page_type(cat_url, html)
            print(f"[Page Classifier] Page type: {page_type}")

            if page_type != "category":
                print(f"[Warning] Expected category page but got: {page_type}")

            product_links = run_navigator_agent(
                html_content=html,
                page_url=cat_url,
            )

            print(f"[Pipeline] Found {len(product_links)} product links from {cat_url}")

            if not product_links:
                print("[Warning] No product links found on this category page.")

            for product_url in product_links:
                print(f"[Pipeline] Queue product URL: {product_url}")
                insert_url(product_url, "product")

            update_url_status(cat_url, "completed")
            print(f"[Pipeline] Category completed: {cat_url}")

        except Exception as e:
            print(f"[Pipeline Error] Failed processing category {cat_url}: {e}")
            update_url_status(cat_url, "failed")

        time.sleep(REQUEST_DELAY_SECONDS)


def extract_products_from_queue(max_products: int = MAX_POC_PRODUCTS) -> int:
  
    # Phase B:
    # Process pending product URLs, extract structured product data,
    # validate/clean the result, and save it into MySQL.
    
    print("\n--- [Phase B] Extracting Product Data ---")

    products_processed = 0

    while products_processed < max_products:
        prod_url = get_next_pending_url("product")

        if not prod_url:
            print("[Pipeline] No more pending products in queue.")
            break

        print(f"\n[Pipeline] Processing product: {prod_url}")

        try:
            html = fetch_page_with_retry(prod_url)

            page_type = classify_page_type(prod_url, html)
            print(f"[Page Classifier] Page type: {page_type}")

            if page_type != "product":
                print(f"[Warning] Expected product page but got: {page_type}")

            product_model = run_extractor_agent(
                html_content=html,
                product_url=prod_url,
            )

            product_model = validate_and_clean_product(product_model)

            save_product(product_model)

            print(f"[Success] Extracted and saved: {product_model.product_name}")

            update_url_status(prod_url, "completed")
            products_processed += 1

        except Exception as e:
            print(f"[Pipeline Error] Failed processing product {prod_url}: {e}")
            update_url_status(prod_url, "failed")

        time.sleep(REQUEST_DELAY_SECONDS)

    return products_processed


def run_pipeline() -> None:

    # Main pipeline:
    # 1. Initialize database and seed categories.
    # 2. Discover product URLs from category pages.
    # 3. Extract structured product data from product pages.

    bootstrap_system()

    discover_product_urls_from_categories()

    products_processed = extract_products_from_queue(MAX_POC_PRODUCTS)

    print(
        f"\nPOC Execution Finished! "
        f"Processed {products_processed} products into MySQL."
    )


if __name__ == "__main__":
    run_pipeline()