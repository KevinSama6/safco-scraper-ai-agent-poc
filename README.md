# Safco Dental Product Scraping AI Agent POC

## Overview

This project is a working Proof of Concept (POC) for an Artificial Intelligence (AI) assisted product scraping system.

The goal is to scrape product information from the Safco Dental Supply website, extract structured product catalog data, and store/export the result in a usable format.

The POC focuses on the two required categories:

* Sutures & Surgical Products
  https://www.safcodental.com/catalog/sutures-surgical-products

* Dental Exam Gloves
  https://www.safcodental.com/catalog/gloves

This project is not meant to be a complete production crawler. It is a small working prototype that shows the main workflow can run end to end.

---

## What This Project Does

The current prototype can:

* Start from the two required category pages
* Fetch rendered page content using Playwright
* Discover product detail page Uniform Resource Locators (URLs)
* Store category and product URLs in a MySQL queue
* Process pending product pages
* Extract structured product data with a Large Language Model (LLM)
* Validate the extracted structure with Pydantic
* Save product records into MySQL
* Export sample output to Comma-Separated Values (CSV) and JavaScript Object Notation (JSON)

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
* `scraper.py`: fetches rendered HyperText Markup Language (HTML) using Playwright
* `agents.py`: contains the Navigator Agent and Extractor Agent
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
Pydantic Product Model
        |
        v
MySQL Products Table
        |
        v
CSV / JSON Export
```

The workflow uses a MySQL queue table to track each URL as `pending`, `completed`, or `failed`. This allows the prototype to resume work and avoid processing the same URL multiple times.

---

## Agent Responsibilities

### Navigator Agent

The Navigator Agent is responsible for finding product detail page URLs from category pages.

It uses rule-based HTML parsing first because this is faster, cheaper, and more predictable. The Large Language Model (LLM) can be used as a fallback when the page structure is harder to parse.

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
* Extract structured fields based on the Pydantic schema
* Return a validated product object
* Support product variants when visible on the page

Fields extracted include:

* Product name
* Brand or manufacturer
* Category hierarchy
* Product URL
* Description
* Specifications
* Image URLs
* Alternative products
* Variants, including Stock Keeping Unit (SKU), size, price, and availability

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

Stock Keeping Unit (SKU) means the item code or product variant code. In the POC, obvious invalid SKU values such as `0`, `1`, empty values, `null`, and `N/A` are filtered during export.

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

The pipeline will initialize the database, insert the two seed categories, discover product URLs, extract product data, and save results into MySQL.

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

The POC limits the number of extracted product pages to keep runtime and API cost controlled.

```python
MAX_POC_PRODUCTS = 5
```

This value can be increased to process more product pages.

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

---

## Current Limitations

This is a POC, so there are some limitations:

* It only processes a limited number of products by default.
* Pagination support can be expanded further.
* Some prices or availability values may not be publicly visible.
* Some SKU values may require stronger validation.
* The system starts from two predefined seed categories instead of crawling the whole site.
* It does not yet include parallel workers.
* It does not yet include a monitoring dashboard.
* It does not yet include automated tests.

---

## Failure Handling

The `urls_queue` table provides basic failure handling.

Each URL has a status:

* `pending`
* `completed`
* `failed`

If a page fails, the pipeline marks it as `failed` and continues processing other URLs. This makes it easier to inspect or retry failed pages later.

Possible future improvements:

* Retry count
* Failure reason column
* Exponential backoff
* Dead-letter queue
* Alerting for repeated failures

---

## Scaling to Production

To move this POC toward production, I would add:

* Full pagination handling
* More rule-based validation for SKU, price, availability, and product variants
* Retry logic with exponential backoff
* Structured logging
* Run IDs and processing metrics
* Parallel workers that process pending product URLs from the queue
* Docker deployment
* Cloud scheduler or workflow orchestration
* Managed secrets for API keys and database passwords

The current MySQL queue design already supports a basic path toward scaling because pending product URLs can be processed by one or more workers.

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

I used a hybrid approach instead of relying only on Artificial Intelligence (AI).

Rule-based parsing is used where it is reliable, such as product URL discovery. The Large Language Model (LLM) is used for product detail extraction, where the page structure can be less consistent and the output needs to be normalized.

This keeps the system practical, easier to debug, and less expensive to run.

---

## Example Run

```text
[DB] MySQL tables initialized successfully.
[Pipeline] System bootstrapped with seed categories.

--- [Phase A] Discovering Product URLs from Categories ---
[Pipeline] Queue product URL: https://www.safcodental.com/product/crave-trade
[Pipeline] Queue product URL: https://www.safcodental.com/product/compac-nitrile-exam-gloves
[Pipeline] Category completed: https://www.safcodental.com/catalog/gloves

--- [Phase B] Extracting Product Data ---
[Pipeline] Processing product: https://www.safcodental.com/product/crave-trade
[Success] Extracted and saved: Crave

POC Execution Finished! Processed 5 products into MySQL.
```

---

## Submission Contents

This repository includes:

* Source code
* Setup and execution instructions
* MySQL storage logic
* Sample CSV output
* Sample JSON output
* Notes on limitations and production improvements
