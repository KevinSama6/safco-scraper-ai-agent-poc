import os
import json
import csv
import ast
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv


load_dotenv()


OUTPUT_DIR = Path("output")
CSV_OUTPUT_PATH = OUTPUT_DIR / "sample_products.csv"
JSON_OUTPUT_PATH = OUTPUT_DIR / "sample_products.json"


def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "safco_scraper"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
    )


def safe_parse_data(value):
    """
    Parse product data stored in MySQL.

    Supports:
    1. Standard JSON string
    2. Python dict-style string, for example {'product_name': 'Alasta Pro'}
    3. Already parsed dict
    """
    if value is None:
        return {}

    if isinstance(value, dict):
        return value

    try:
        return json.loads(value)
    except Exception:
        pass

    try:
        return ast.literal_eval(value)
    except Exception:
        return {}


def normalize_product_row(row):
    product_url = row.get("product_url")
    updated_at = row.get("updated_at")

    data = safe_parse_data(row.get("data"))

    variants = data.get("variants", [])
    image_urls = data.get("image_urls", [])
    category_hierarchy = data.get("category_hierarchy", [])
    alternative_products = data.get("alternative_products", [])
    specifications = data.get("specifications", {})

    first_variant = variants[0] if variants else {}

    return {
        "product_name": data.get("product_name"),
        "brand": data.get("brand"),
        "product_url": data.get("product_url") or product_url,
        "category_hierarchy": (
            " > ".join(category_hierarchy)
            if isinstance(category_hierarchy, list)
            else category_hierarchy
        ),
        "description": data.get("description"),
        "sku": clean_sku(first_variant.get("sku")),
        "size_or_color": first_variant.get("size_or_color"),
        "price": first_variant.get("price"),
        "availability": first_variant.get("availability"),
        "specifications": json.dumps(specifications, ensure_ascii=False),
        "image_urls": json.dumps(image_urls, ensure_ascii=False),
        "alternative_products": json.dumps(alternative_products, ensure_ascii=False),
        "variants": json.dumps(variants, ensure_ascii=False),
        "updated_at": str(updated_at) if updated_at else None,
    }

def clean_sku(sku):
    if sku is None:
        return None

    sku = str(sku).strip()

    invalid_values = {"", "0", "1", "none", "null", "n/a", "na"}

    if sku.lower() in invalid_values:
        return None

    return sku

def fetch_products(limit=50):
    connection = get_db_connection()
    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT product_url, data, updated_at
            FROM products
            ORDER BY updated_at DESC
            LIMIT %s
        """

        cursor.execute(query, (limit,))
        return cursor.fetchall()

    finally:
        if cursor:
            cursor.close()
        connection.close()


def export_to_csv(products):
    if not products:
        print("[Export] No products found. CSV file was not created.")
        return

    fieldnames = list(products[0].keys())

    with open(CSV_OUTPUT_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(products)

    print(f"[Export] CSV saved to: {CSV_OUTPUT_PATH}")


def export_to_json(raw_rows):
    output = []

    for row in raw_rows:
        data = safe_parse_data(row.get("data"))

        if "product_url" not in data:
            data["product_url"] = row.get("product_url")

        if row.get("updated_at"):
            data["updated_at"] = str(row.get("updated_at"))

        output.append(data)

    with open(JSON_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"[Export] JSON saved to: {JSON_OUTPUT_PATH}")


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    raw_rows = fetch_products(limit=50)

    if not raw_rows:
        print("[Export] No products found in database.")
        return

    normalized_products = [normalize_product_row(row) for row in raw_rows]

    export_to_csv(normalized_products)
    export_to_json(raw_rows)

    print(f"[Export] Finished. Exported {len(normalized_products)} products.")


if __name__ == "__main__":
    main()