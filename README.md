# Safco Dental Product Scraping AI Agent POC

## Overview

This project is a working POC for an AI-assisted product scraping system.

The goal is to scrape product information from the Safco Dental Supply website, extract structured product catalog data, store the result in MySQL, and export sample data to CSV and JSON.

The POC focuses on the two required categories:

* Sutures & Surgical Products
  https://www.safcodental.com/catalog/sutures-surgical-products

* Dental Exam Gloves
  https://www.safcodental.com/catalog/gloves

This is not intended to be a full production crawler yet. It is a small working prototype that proves the main workflow can run end to end.

---

## What This Project Does

The current prototype can:

* Start from the two required category pages
* Fetch rendered page content using Playwright
* Classify pages as category, product, or unknown
* Discover product detail page URLs
* Store category and product URLs in a MySQL queue
* Process pending product pages
* Extract structured product data using an LLM
* Validate the extracted structure with Pydantic
* Clean obvious invalid SKU values
* Save product records into MySQL
* Export sample output to CSV and JSON

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

Main files:

* `pipeline.py`: controls the full scraping workflow
* `scraper.py`: fetches rendered HTML using Playwright and includes retry logic
* `agents.py`: contains the Page Classifier, Navigator Agent, and Extractor Agent
* `validators.py`: cleans and validates extracted product data
* `models.py`: defines the Pydantic product schema
* `db.py`: handles MySQL tables, queue operations, and product storage
* `export_sample.py`: exports product data from MySQL to CSV and JSON

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

This project separates responsibilities instead of using one monolithic script.

### Page Classifier

The Page Classifier is a lightweight rule-based component.

It checks the URL and page content to classify a page as:

* `category`
* `product`
* `unknown`

This helps the pipeline verify that the expected type of page is being processed.

### Navigator Agent

The Navigator Agent is responsible for finding product detail page URLs from category pages.

It uses rule-based HTML parsing first because this is faster, cheaper, and more predictable. The LLM can be used as a fallback when product links are not found with rules alone.

Responsibilities:

* Read category page HTML
* Find product page links
* Convert relative links into absolute URLs
* Filter out non-product links
* Return product URLs to the pipeline

### Extractor Agent

The Extractor Agent is responsible for extracting product data from product detail pages.

Responsibilities:

* Read product page HTML
* Extract structured product fields
* Return a validated Pydantic product object
* Support product variants when visible on the page

Extracted fields include:

* Product name
* Brand or manufacturer
* Category hierarchy
* Product URL
* Description
* Specifications
* Image URLs
* Alternative products
* Variants, including SKU, size, price, and availability

### Validator / Deduplicator

The Validator / Deduplicator performs lightweight cleanup after extraction.

Current validation includes:

* Cleaning invalid SKU values such as `0`, `1`, empty strings, `null`, and `N/A`
* Keeping uncertain or missing fields as `None` instead of forcing fake values
* Using MySQL primary keys to prevent duplicate URLs and duplicate product records

### Retry / Recovery Logic

The scraper includes basic retry logic when fetching pages.

If a fetch attempt fails, the system retries a limited number of times before marking the URL as failed in the queue. This allows the pipeline to continue processing other URLs instead of stopping completely.

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

The pipeline will initialize the database, insert the two seed categories, discover product URLs, extract product data, clean the result, and save products into MySQL.

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

* `sample_products.csv`
* `sample_products.json`

The CSV file is useful for quick review in spreadsheet tools.
The JSON file keeps nested data such as variants, image URLs, and specifications.

Some fields may be empty if they are not publicly visible on the product page or cannot be confidently extracted.

---

## Current Limitations

This is a POC, so there are some limitations:

* It only processes a limited number of products by default.
* Pagination support can be expanded further.
* Some prices or availability values may not be publicly visible.
* Some product pages may have fewer visible fields than others.
* Some SKU values may require stronger rule-based validation in production.
* The system starts from two predefined seed categories instead of crawling the whole site.
* It does not yet include parallel workers.
* It does not yet include a monitoring dashboard.
* It does not yet include automated tests.

---

## Failure Handling

The `urls_queue` table provides basic failure handling.

Each URL has one of the following statuses:

* `pending`
* `completed`
* `failed`

If a page fails, the pipeline marks it as `failed` and continues processing other URLs.

Possible future improvements:

* Retry count stored in the database
* Failure reason column
* Exponential backoff
* Dead-letter queue
* Alerting for repeated failures

---

## Production-Minded Design

This POC includes several basic production-minded components, but it is not a fully production-ready crawler.

Implemented in this POC:

- Basic rate limiting through request delay
- Basic retry logic for page fetching
- Error handling with try/except blocks
- URL status tracking with pending, completed, and failed
- Resumability through the MySQL urls_queue table
- Deduplication through primary keys and INSERT IGNORE
- Idempotent product writes through ON DUPLICATE KEY UPDATE
- Environment-based secrets through .env
- Sample export to CSV and JSON

Planned for production:

- Structured logging instead of print logs
- Full config-driven execution for seed URLs, product limits, delays, and model names
- Full pagination crawling
- Retry counters and failure reason tracking in MySQL
- Monitoring dashboard
- Docker deployment
- Cloud scheduler or workflow orchestration

---

## Data Quality Monitoring

For production, I would monitor:

* Number of products extracted
* Number of failed URLs
* Missing product name rate
* Missing SKU rate
* Missing price rate
* Duplicate product URL count
* Empty variant count
* Invalid price format count
* Average processing time per page
* LLM token usage and cost

These checks would help detect extraction issues and website layout changes.

---

## Why This Approach

I used a hybrid approach instead of relying only on AI.

Rule-based parsing is used where it is reliable, such as product URL discovery and page classification. The LLM is used for product detail extraction, where the page structure can be less consistent and the output needs to be normalized.

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

This repository includes:

* Source code
* Setup and execution instructions
* MySQL storage logic
* Agentic workflow components
* Sample CSV output
* Sample JSON output
* Notes on limitations and production improvements
