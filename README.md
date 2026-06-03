# Safco Dental Product Scraping Artificial Intelligence Agent Proof of Concept (AI Agent POC)

## 1. Project Overview

This project is a working Proof of Concept (POC) for an Artificial Intelligence (AI) assisted product scraping and structured catalog extraction system.

The goal of this project is to demonstrate how an agent-based scraping workflow can discover product pages from Safco Dental Supply category pages, extract structured product information from product detail pages, and store the extracted data in a queryable and exportable format.

The target website is Safco Dental Supply.

The current Proof of Concept (POC) focuses on the following two required categories:

* Sutures & Surgical Products
  https://www.safcodental.com/catalog/sutures-surgical-products

* Dental Exam Gloves
  https://www.safcodental.com/catalog/gloves

This project is not intended to be a full production crawler yet. Instead, it demonstrates a clean working slice of a system that can realistically evolve into a production-ready product catalog extraction pipeline.

---

## 2. Project Goals

The project is designed to show that the system can:

* Start from predefined category pages
* Discover product detail page Uniform Resource Locators (URLs)
* Traverse category pages and product pages
* Extract structured product data
* Normalize extracted data into a consistent schema
* Store results in a MySQL relational database
* Export sample output into Comma-Separated Values (CSV) and JavaScript Object Notation (JSON) files
* Track processing status for resumability and checkpointing
* Separate navigation, extraction, storage, and export responsibilities
* Use Artificial Intelligence (AI) where it provides practical value

---

## 3. High-Level Architecture

The system follows an agent-based pipeline design.

```text
Seed Category Uniform Resource Locators (URLs)
        |
        v
MySQL Uniform Resource Locator (URL) Queue
        |
        v
Navigator Agent
        |
        v
Discovered Product Uniform Resource Locators (URLs)
        |
        v
MySQL Uniform Resource Locator (URL) Queue
        |
        v
Extractor Agent
        |
        v
Structured Product Model
        |
        v
MySQL Products Table
        |
        v
Sample Output Export
```

The main workflow is controlled by `pipeline.py`.

The system first inserts the two target category Uniform Resource Locators (URLs) into a MySQL queue. The Navigator Agent processes category pages and discovers product detail page Uniform Resource Locators (URLs). The Extractor Agent then visits product detail pages, extracts structured product information, validates the result with a Pydantic schema, and saves the output into MySQL.

---

## 4. Project Structure

```text
safco_scraper_poc/
│
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
│
└── output/
    ├── sample_products.csv
    └── sample_products.json
```

### File Responsibilities

| File               | Responsibility                                                                                        |
| ------------------ | ----------------------------------------------------------------------------------------------------- |
| `pipeline.py`      | Main orchestration workflow for the scraping pipeline                                                 |
| `scraper.py`       | Page fetching using Playwright browser automation                                                     |
| `agents.py`        | Navigator Agent and Extractor Agent logic                                                             |
| `models.py`        | Pydantic data models for structured product extraction                                                |
| `db.py`            | MySQL database initialization and database operations                                                 |
| `export_sample.py` | Exports product data from MySQL to Comma-Separated Values (CSV) and JavaScript Object Notation (JSON) |
| `requirements.txt` | Python dependency list                                                                                |
| `.env.example`     | Example environment variable configuration                                                            |
| `output/`          | Sample exported product data                                                                          |

---

## 5. Agent Responsibilities

## 5.1 Navigator Agent

The Navigator Agent is responsible for finding product detail page Uniform Resource Locators (URLs) from category or listing pages.

Current responsibilities:

* Receive HyperText Markup Language (HTML) content from a category page
* Parse the page structure
* Identify product detail page links
* Convert relative links into absolute Uniform Resource Locators (URLs)
* Filter out non-product links such as cart pages, login pages, account pages, image files, Portable Document Format (PDF) files, and category pages
* Return product detail page Uniform Resource Locators (URLs) to the pipeline
* Insert discovered product Uniform Resource Locators (URLs) into the MySQL queue

The Navigator Agent uses a hybrid strategy:

1. Rule-based HyperText Markup Language (HTML) parsing for deterministic and low-cost product link discovery
2. Large Language Model (LLM) fallback when page layouts are irregular or difficult to parse with rules alone

This design avoids using Artificial Intelligence (AI) unnecessarily. Deterministic parsing is used first because it is cheaper, faster, and more predictable. The Large Language Model (LLM) is reserved for cases where it adds practical value.

---

## 5.2 Extractor Agent

The Extractor Agent is responsible for extracting structured product data from product detail pages.

Current responsibilities:

* Receive HyperText Markup Language (HTML) content from a product detail page
* Extract product information according to the Pydantic schema
* Capture product name, brand, category hierarchy, product Uniform Resource Locator (URL), description, specifications, image Uniform Resource Locators (URLs), alternative products, and variants
* Extract variant-level information such as Stock Keeping Unit (SKU), size or color, price, and availability when visible
* Return a validated structured `ProductModel`

The Extractor Agent uses a Large Language Model (LLM) with structured output validation. Pydantic is used to enforce the expected schema.

---

## 6. Data Model

The extracted product data is normalized into a structured product schema.

## 6.1 Product Model

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

## 6.2 Product Variant Model

```python
class ProductVariant(BaseModel):
    sku: Optional[str]
    size_or_color: Optional[str]
    price: Optional[float]
    availability: Optional[str]
```

## 6.3 Stock Keeping Unit (SKU)

Stock Keeping Unit (SKU) refers to the item code or product variant code used to identify a specific sellable product or variant.

For example, one glove product may have multiple sizes, and each size may have a different Stock Keeping Unit (SKU).

In this Proof of Concept (POC), Stock Keeping Unit (SKU) extraction is supported when the product page clearly exposes a visible item number, item code, product code, catalog number, or Stock Keeping Unit (SKU). Obvious invalid values such as `0`, `1`, empty strings, `null`, and `N/A` are filtered during export.

In a production version, Stock Keeping Unit (SKU) validation would be strengthened with additional rule-based checks and confidence scoring.

---

## 7. Database Design

The project uses MySQL as the persistence layer.

There are two main tables:

1. `urls_queue`
2. `products`

---

## 7.1 Uniform Resource Locator Queue Table

The `urls_queue` table stores category and product Uniform Resource Locators (URLs) and tracks their processing status.

Example fields:

```text
url
url_type
status
updated_at
```

Field descriptions:

| Field        | Description                                            |
| ------------ | ------------------------------------------------------ |
| `url`        | Category or product Uniform Resource Locator (URL)     |
| `url_type`   | Either `category` or `product`                         |
| `status`     | Processing status: `pending`, `completed`, or `failed` |
| `updated_at` | Last update timestamp                                  |

This table supports:

* Resumability
* Checkpointing
* Deduplication
* Failure recovery
* Future worker-based scaling

---

## 7.2 Products Table

The `products` table stores extracted product records.

Example fields:

```text
product_url
data
updated_at
```

Field descriptions:

| Field         | Description                                                                 |
| ------------- | --------------------------------------------------------------------------- |
| `product_url` | Unique product detail page Uniform Resource Locator (URL)                   |
| `data`        | Structured product payload stored as JavaScript Object Notation (JSON) text |
| `updated_at`  | Last update timestamp                                                       |

The `product_url` field is used as the primary key. This makes writes idempotent, meaning the same product can be processed multiple times without creating duplicate records.

---

## 8. Setup Instructions

## 8.1 Create a Python Virtual Environment

```bash
python -m venv venv
```

Activate the virtual environment.

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

macOS or Linux:

```bash
source venv/bin/activate
```

---

## 8.2 Install Python Dependencies

```bash
python -m pip install -r requirements.txt
```

Install the Playwright Chromium browser:

```bash
python -m playwright install chromium
```

---

## 8.3 Configure Environment Variables

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

Important:

The `.env` file should not be committed to GitHub. It may contain sensitive values such as an OpenAI Application Programming Interface (API) key and a MySQL password.

---

## 8.4 Initialize MySQL

Create the database if it does not already exist:

```sql
CREATE DATABASE safco_scraper;
```

The application also creates the required tables automatically when `pipeline.py` runs.

---

## 8.5 Run the Pipeline

```bash
python pipeline.py
```

The pipeline will:

1. Initialize the MySQL database tables
2. Insert the two required seed category Uniform Resource Locators (URLs)
3. Fetch category pages using Playwright
4. Discover product detail page Uniform Resource Locators (URLs)
5. Insert product Uniform Resource Locators (URLs) into the queue
6. Fetch product detail pages
7. Extract structured product data using the Extractor Agent
8. Save product data into MySQL

---

## 8.6 Export Sample Output

After running the pipeline, export the sample product data:

```bash
python export_sample.py
```

This creates:

```text
output/sample_products.csv
output/sample_products.json
```

The Comma-Separated Values (CSV) file provides a flat view for quick review in spreadsheet tools.

The JavaScript Object Notation (JSON) file preserves nested fields such as product variants, image Uniform Resource Locators (URLs), and specifications.

---

## 9. Runtime Controls

The current Proof of Concept (POC) includes a product processing limit:

```python
MAX_POC_PRODUCTS = 10
```

This controls runtime, token usage, and Application Programming Interface (API) cost during demonstration.

To process more products, increase the value.

The pipeline also includes a delay between requests:

```python
REQUEST_DELAY_SECONDS = 2
```

This helps reduce request frequency and avoids putting unnecessary load on the target website.

---

## 10. Sample Output

Sample output is included in the `output/` folder.

Expected files:

```text
output/sample_products.csv
output/sample_products.json
```

Example output fields:

```text
product_name
brand
product_url
sku
size_or_color
price
availability
category_hierarchy
specifications
image_urls
alternative_products
variants
description
updated_at
```

The sample output demonstrates that the system can extract products from the required categories and store the results in a structured format.

Some values may be empty if they are not publicly visible on the product page.

---

## 11. Validation and Data Cleaning

The current Proof of Concept (POC) includes lightweight validation and data cleaning.

Current validation includes:

* Pydantic schema validation for structured product output
* Uniform Resource Locator (URL) deduplication using MySQL primary keys
* Queue status tracking with `pending`, `completed`, and `failed`
* Idempotent product writes using `ON DUPLICATE KEY UPDATE`
* Export-level cleanup for invalid Stock Keeping Unit (SKU) values such as `0`, `1`, empty strings, `null`, and `N/A`

Production-level validation could include:

* Rule-based Stock Keeping Unit (SKU) extraction from visible labels such as `Item #`, `Product Code`, `Catalog #`, or `SKU`
* Missing-field checks
* Price format validation
* Availability normalization
* Image Uniform Resource Locator (URL) validation
* Confidence scoring for Large Language Model (LLM) extracted fields
* Manual review queue for low-confidence records

---

## 12. Failure Handling and Resumability

The system uses the `urls_queue` table to support failure handling and resumability.

Each Uniform Resource Locator (URL) has one of the following statuses:

```text
pending
completed
failed
```

If a category page or product page fails, the pipeline marks that Uniform Resource Locator (URL) as `failed` instead of stopping the entire run.

This allows the system to:

* Continue processing other Uniform Resource Locators (URLs)
* Inspect failed Uniform Resource Locators (URLs) later
* Retry failed Uniform Resource Locators (URLs) in a future run
* Avoid duplicate processing of completed Uniform Resource Locators (URLs)

Future improvements could include:

* Retry counters
* Exponential backoff
* Failure reason logging
* Dead-letter queue
* Alerting for repeated failures

---

## 13. Current Limitations

This project is a Proof of Concept (POC), so it has several known limitations:

* The default run only processes a limited number of product pages.
* Some product prices or availability values may not be publicly visible.
* Some product fields may require login or additional website interaction.
* Stock Keeping Unit (SKU) extraction may need stricter rule-based validation in production.
* Pagination support can be extended further for full category coverage.
* The current database schema stores nested product data as JavaScript Object Notation (JSON) text for flexibility.
* The crawler currently starts from predefined seed categories instead of discovering the entire site map.
* The system does not yet include distributed workers.
* The system does not yet include a full monitoring dashboard.
* The system does not yet include automated tests.

---

## 14. Production Hardening Plan

To evolve this Proof of Concept (POC) into a production-ready system, I would improve the following areas.

---

## 14.1 Rate Limiting

Add configurable per-domain rate limits to control request frequency and reduce load on the target website.

---

## 14.2 Retry Logic

Add retry policies with exponential backoff for temporary failures such as network errors, page load timeouts, and transient Application Programming Interface (API) errors.

---

## 14.3 Idempotency

Use unique constraints on product Uniform Resource Locators (URLs) and product identifiers to prevent duplicate records when the pipeline is rerun.

The current Proof of Concept (POC) already uses primary keys and `ON DUPLICATE KEY UPDATE` for basic idempotent writes.

---

## 14.4 Pagination Handling

Extend the Navigator Agent to detect and follow pagination links on category pages.

This would allow the system to crawl all listing pages under a category instead of only the initially loaded product links.

---

## 14.5 Stronger Validation

Add stricter rule-based validators for:

* Stock Keeping Unit (SKU)
* Product name
* Price
* Availability
* Image Uniform Resource Locators (URLs)
* Product variant completeness

---

## 14.6 Observability

Add structured logging, run identifiers, processing metrics, and failure summaries.

Useful metrics include:

* Number of category pages processed
* Number of product Uniform Resource Locators (URLs) discovered
* Number of product pages completed
* Number of failed Uniform Resource Locators (URLs)
* Extraction success rate
* Missing field rate
* Average processing time per page
* Token usage
* Application Programming Interface (API) cost

---

## 14.7 Secrets Management

Move all credentials into environment variables or a managed secret store.

Sensitive values include:

* OpenAI Application Programming Interface (API) key
* MySQL password
* Any future cloud service credentials

No secrets should be committed to source control.

---

## 14.8 Deployment Path

A production version could be deployed using:

* Docker containerization
* Google Cloud Run
* Amazon Web Services Elastic Container Service (AWS ECS)
* Azure Container Apps
* Managed MySQL or PostgreSQL
* Cloud Scheduler, cron jobs, Apache Airflow, or GitHub Actions

---

## 14.9 Data Quality Monitoring

Data quality can be monitored through validation checks such as:

* Missing product name rate
* Missing Stock Keeping Unit (SKU) rate
* Missing image Uniform Resource Locator (URL) rate
* Duplicate product Uniform Resource Locator (URL) count
* Invalid price format count
* Empty product variant count
* Failed extraction count
* Category coverage by run
* Change detection between runs

---

## 15. Why This Approach

This project separates navigation, extraction, storage, and export responsibilities.

The system does not use Artificial Intelligence (AI) for every step. Instead, it uses deterministic parsing where possible and applies Large Language Model (LLM) extraction where it provides practical value.

This makes the system:

* More reliable
* More cost-efficient
* Easier to debug
* Easier to extend
* More aligned with production engineering practices

The MySQL queue design also makes the pipeline more production-minded because it supports resumability, deduplication, checkpointing, and future worker-based scaling.

---

## 16. Alignment with Strong Submission Criteria

This Proof of Concept (POC) is designed to match the expected strong-submission criteria.

* It crawls the two required Safco category pages and discovers product detail pages automatically.
* It uses Playwright to handle modern and dynamic page rendering before extraction.
* It stores normalized product data in MySQL and exports sample results to Comma-Separated Values (CSV) and JavaScript Object Notation (JSON).
* It separates responsibilities across a Navigator Agent, an Extractor Agent, a database queue, and an export layer.
* It uses Artificial Intelligence (AI) practically. Rule-based parsing is used for product link discovery when possible, while the Large Language Model (LLM) is used for structured extraction from product detail pages.
* It includes production-hardening considerations such as rate limiting, retry handling, checkpointing, deduplication, idempotent writes, secrets management, and data quality monitoring.

---

## 17. Example Run

Example terminal output:

```text
[DB] MySQL tables initialized successfully.
[Pipeline] System bootstrapped with seed categories.

--- [Phase A] Discovering Product URLs from Categories ---
[Pipeline] Processing category: https://www.safcodental.com/catalog/gloves
[Pipeline] Queue product URL: https://www.safcodental.com/product/crave-trade
[Pipeline] Queue product URL: https://www.safcodental.com/product/compac-nitrile-exam-gloves
[Pipeline] Category completed: https://www.safcodental.com/catalog/gloves

--- [Phase B] Extracting Product Data ---
[Pipeline] Processing product: https://www.safcodental.com/product/crave-trade
[Success] Extracted and saved: Crave

POC Execution Finished! Processed 5 products into MySQL.
```

---

## 18. Repository Submission Contents

The repository includes:

```text
Source code
README.md
requirements.txt
.env.example
.gitignore
Sample output files
```

The project is designed as a working Proof of Concept (POC) that can be run locally and extended into a production-ready product scraping and catalog extraction system.
