# Safco Dental Product Scraping AI Agent POC

## Overview

This project is a working POC for an AI-assisted product scraping system.

The goal is to scrape product information from the Safco Dental Supply website, extract structured product catalog data, store the result in MySQL, and export sample data to CSV and JSON.

The POC focuses on the two required categories:

- Sutures & Surgical Products  
  https://www.safcodental.com/catalog/sutures-surgical-products

- Dental Exam Gloves  
  https://www.safcodental.com/catalog/gloves

This is not intended to be a full production crawler yet. It is a small working prototype that proves the main workflow can run end to end.

---

## What This Project Does

The current prototype starts from the two required category pages, fetches rendered page content using Playwright, classifies pages as category or product pages, discovers product detail URLs, and stores them in a MySQL queue.

After that, it processes pending product pages, extracts structured product data using an LLM, validates the extracted structure with Pydantic, cleans obvious invalid SKU values, saves product records into MySQL, and exports sample output to CSV and JSON.

---

## Project Structure

```text
safco_scraper_poc/
├── agents.py
├── db.py
├── export_sample.py
├── models.py
├── pipeline.py
├── scraper.py
├── validators.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
└── output/
    ├── sample_products.csv
    └── sample_products.json
```

The main workflow is controlled by `pipeline.py`. Page fetching and retry logic are handled in `scraper.py`. The agent logic is inside `agents.py`, including the Page Classifier, Navigator Agent, and Extractor Agent.

Product schemas are defined in `models.py`, validation and cleanup are handled in `validators.py`, and MySQL operations are managed in `db.py`. The `export_sample.py` script exports saved product data into CSV and JSON files.

---

## Architecture

```text
Seed Category URLs
        |
        v
MySQL URL Queue
        |
        v
Fetch Rendered HTML
        |
        v
Page Classifier
        |
        v
Navigator Agent
        |
        v
Product URLs
        |
        v
MySQL URL Queue
        |
        v
Extractor Agent
        |
        v
Validator / Deduplicator
        |
        v
MySQL Products Table
        |
        v
CSV / JSON Export
```

The system uses a MySQL queue table to track each URL as `pending`, `completed`, or `failed`. This gives the POC basic checkpointing, deduplication, and resumability.

---

## Agentic Workflow

This project separates the scraping workflow into several simple agent-like components instead of using one large script.

The Page Classifier checks the URL and page content to decide whether a page is a `category`, `product`, or `unknown` page. This helps the pipeline make sure the expected type of page is being processed.

The Navigator Agent is responsible for reading category page HTML and finding product detail page URLs. It uses rule-based HTML parsing first because this is faster, cheaper, and easier to debug. The LLM can be used as a fallback when product links are not found with rules alone.

The Extractor Agent reads product detail page HTML and extracts structured product data, including product name, brand, category hierarchy, product URL, description, specifications, image URLs, alternative products, and visible product variants such as SKU, size, price, and availability.

After extraction, the Validator / Deduplicator performs lightweight cleanup. For example, it removes invalid SKU values such as `0`, `1`, empty strings, `null`, and `N/A`. Missing or uncertain values are kept as `None` instead of being replaced with fake data. MySQL primary keys are also used to prevent duplicate URLs and duplicate product records.

---

## Data Schema

### ProductModel

```python
class ProductModel(BaseModel):
    product_name: str
    brand: Optional[str]
    category_hierarchy: List[str]
    product_url: str
    description: Optional[str]
    specifications: Optional[dict]
    image_urls: List[str]
    alternative_products: List[str]
    variants: List[ProductVariant]
```

### ProductVariant

```python
class ProductVariant(BaseModel):
    sku: Optional[str]
    size_or_color: Optional[str]
    price: Optional[float]
    availability: Optional[str]
```

SKU means the item code or product variant code. In this POC, SKU is only kept when it appears to be a valid visible product code. Obvious invalid values are removed during validation and export.

---

## Database Tables

### urls_queue

This table tracks category and product URLs.

| Field        | Description                         |
| ------------ | ----------------------------------- |
| `url`        | Category or product URL             |
| `url_type`   | `category` or `product`             |
| `status`     | `pending`, `completed`, or `failed` |
| `updated_at` | Last update time                    |

### products

This table stores extracted product data.

| Field         | Description                                |
| ------------- | ------------------------------------------ |
| `product_url` | Product detail page URL                    |
| `data`        | Extracted product data stored as JSON text |
| `updated_at`  | Last update time                           |

---

## Setup

### 1. Create a virtual environment

```bash
python -m venv venv
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
source venv/bin/activate
```

### 2. Install dependencies

```bash
python -m pip install -r requirements.txt
```

Install Playwright Chromium:

```bash
python -m playwright install chromium
```

### 3. Configure environment variables

Create a `.env` file based on `.env.example`.

Example:

```env
OPENAI_API_KEY=your_openai_api_key_here

MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=safco_scraper
MYSQL_PORT=3306
```

Do not commit the `.env` file to GitHub.

### 4. Run the pipeline

```bash
python pipeline.py
```

The pipeline initializes the database, inserts the two seed category URLs, discovers product URLs, extracts product data, cleans the result, and saves products into MySQL.

### 5. Export sample output

```bash
python export_sample.py
```

This creates:

```text
output/sample_products.csv
output/sample_products.json
```

---

## Runtime Control

The POC limits the number of extracted product pages to control runtime and API cost.

```python
MAX_POC_PRODUCTS = 5
```

This value can be increased to process more products.

The pipeline also includes a small delay between requests:

```python
REQUEST_DELAY_SECONDS = 2
```

---

## Sample Output

Sample output is included under the `output/` folder:

- `sample_products.csv`
- `sample_products.json`

The CSV file is useful for quick review in spreadsheet tools. The JSON file keeps nested data such as variants, image URLs, and specifications.

Some fields may be empty if they are not publicly visible on the product page or cannot be confidently extracted.

---

## Current Limitations

This is a POC, so it only processes a limited number of products by default. Pagination support can be expanded further, and some prices, availability values, or product details may not be publicly visible on every product page. Some SKU values may also require stronger rule-based validation in a production version.

The current version starts from two predefined seed categories instead of crawling the whole website. It also does not yet include parallel workers, a monitoring dashboard, or automated tests.

---

## Failure Handling

The `urls_queue` table provides basic failure handling. Each URL has one of the following statuses: `pending`, `completed`, or `failed`.

If a page fails, the pipeline marks it as `failed` and continues processing other URLs instead of stopping the whole run. In a production version, this could be improved with retry counts, failure reason tracking, exponential backoff, a dead-letter queue, and alerting for repeated failures.

---

## Scaling to Production

To move this POC toward production, I would expand pagination handling, add stronger rule-based validation for SKU, price, availability, and product variants, and store retry counters and failure reasons in the database.

I would also add structured logging, run IDs, processing metrics, Docker deployment, cloud scheduling, managed secrets, and parallel workers that process pending product URLs from the queue.

The current MySQL queue design provides a basic path toward scaling because pending product URLs can be processed by one or more workers.

---

## Data Quality Monitoring

For production, I would monitor the number of products extracted, failed URLs, missing product names, missing SKU values, missing prices, duplicate product URLs, empty variants, invalid price formats, average processing time per page, and LLM token usage or cost.

These checks would help detect extraction issues and website layout changes.

---

## Why This Approach

I used a hybrid approach instead of relying only on AI. Rule-based parsing is used where it is reliable, such as product URL discovery and page classification. The LLM is used for product detail extraction, where the page structure can be less consistent and the output needs to be normalized.

This keeps the system practical, easier to debug, and less expensive to run.

---

## Example Run

```text
[DB] MySQL tables initialized successfully.
[Pipeline] System bootstrapped with seed categories.

--- [Phase A] Discovering Product URLs from Categories ---
[Page Classifier] Page type: category
[Pipeline] Queue product URL: https://www.safcodental.com/product/crave-trade
[Pipeline] Queue product URL: https://www.safcodental.com/product/compac-nitrile-exam-gloves
[Pipeline] Category completed: https://www.safcodental.com/catalog/gloves

--- [Phase B] Extracting Product Data ---
[Pipeline] Processing product: https://www.safcodental.com/product/crave-trade
[Page Classifier] Page type: product
[Success] Extracted and saved: Crave

POC Execution Finished! Processed 5 products into MySQL.
```

---

## Submission Contents

This repository includes the source code, setup instructions, MySQL storage logic, agentic workflow components, sample CSV output, sample JSON output, and notes on limitations and production improvements.
