import os
import re
from urllib.parse import urljoin, urlparse
from typing import List

from dotenv import load_dotenv
from bs4 import BeautifulSoup
from openai import OpenAI
import instructor
from pydantic import BaseModel, Field

from models import ProductModel


load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise ValueError("OPENAI_API_KEY is missing. Please set it in your environment variables.")

client = instructor.from_openai(OpenAI(api_key=API_KEY))


class URLItem(BaseModel):
    url: str = Field(description="The absolute product detail page URL")


class CategoryPageExtraction(BaseModel):
    product_urls: List[URLItem] = Field(
        description="List of all product detail page URLs found on the page"
    )


def clean_html_for_llm(html_content: str) -> str:
 
    # Remove unnecessary script, style, and SVG content before sending HTML to the LLM.
    # This reduces token usage and improves extraction quality.
    
    html = re.sub(r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>", "", html_content)
    html = re.sub(r"<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>", "", html)
    html = re.sub(r"<svg\b[^<]*(?:(?!<\/svg>)<[^<]*)*<\/svg>", "", html)
    html = re.sub(r"\s+", " ", html)

    return html[:45000]


# ==========================================
# Page Classifier
# ==========================================
def classify_page_type(url: str, html_content: str) -> str:
  
    # Classify a page as category, product, or unknown.
    # This is a lightweight rule-based classifier.
    # It avoids unnecessary LLM calls for simple page type detection.
    
    lower_url = url.lower()
    lower_html = html_content.lower()

    if "/catalog/" in lower_url:
        return "category"

    if "/product/" in lower_url:
        return "product"

    product_signals = [
        "add to cart",
        "item #",
        "item number",
        "sku",
        "product code",
        "availability",
        "price",
    ]

    if any(signal in lower_html for signal in product_signals):
        return "product"

    return "unknown"


def is_likely_product_url(url: str) -> bool:
   
    # Determine whether a URL is likely to be a product detail page.
    
    parsed = urlparse(url)
    path = parsed.path.lower()

    bad_patterns = [
        "/cart",
        "/login",
        "/account",
        "/search",
        "/contact",
        "/about",
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
        ".pdf",
    ]

    if any(pattern in path for pattern in bad_patterns):
        return False

    product_indicators = [
        "/product/",
        "/products/",
        "/item/",
        "/p/",
    ]

    return any(indicator in path for indicator in product_indicators)


def extract_product_links_rule_based(
    html_content: str,
    page_url: str,
    base_url: str = "https://www.safcodental.com",
) -> List[str]:

    # Extract product detail links from HTML using deterministic parsing.
  
    soup = BeautifulSoup(html_content, "html.parser")
    links = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()

        if not href:
            continue

        absolute_url = urljoin(base_url, href)
        absolute_url = absolute_url.split("#")[0]

        if "safcodental.com" not in absolute_url:
            continue

        if absolute_url == page_url:
            continue

        if is_likely_product_url(absolute_url):
            links.add(absolute_url)

    return sorted(links)


# ==========================================
# Navigator Agent
# ==========================================
def run_navigator_agent(
    html_content: str,
    page_url: str,
    base_url: str = "https://www.safcodental.com",
) -> List[str]:
  
    # Discover product detail page URLs from a category page.

    # The Navigator Agent uses:
    # 1. Rule-based parsing first.
    # 2. LLM fallback only when rule-based parsing finds no product links.
  
    rule_based_links = extract_product_links_rule_based(
        html_content=html_content,
        page_url=page_url,
        base_url=base_url,
    )

    print(f"[Navigator] Rule-based product links found: {len(rule_based_links)}")

    for link in rule_based_links[:10]:
        print(f"  - {link}")

    if rule_based_links:
        return rule_based_links

    cleaned_html = clean_html_for_llm(html_content)

    prompt = f"""
You are a Navigator Agent for an e-commerce scraper.

Analyze the HTML content of this category or listing page and extract all product detail links.

Rules:
- Only return URLs for specific product detail pages.
- Do not return category pages.
- Do not return cart, login, search, image, PDF, or account pages.
- Convert relative URLs into absolute URLs using this base URL: {base_url}

Current page URL:
{page_url}

HTML Content:
{cleaned_html}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_model=CategoryPageExtraction,
            messages=[{"role": "user", "content": prompt}],
        )

        llm_links = [item.url for item in response.product_urls]
        llm_links = [url for url in llm_links if is_likely_product_url(url)]

        print(f"[Navigator] LLM fallback product links found: {len(llm_links)}")

        for link in llm_links[:10]:
            print(f"  - {link}")

        return llm_links

    except Exception as e:
        print(f"[Agent Error] Navigator failed: {e}")
        return []


# ==========================================
# Extractor Agent
# ==========================================
def run_extractor_agent(html_content: str, product_url: str) -> ProductModel:
  
    # Extract structured product data from a product detail page.
   
    cleaned_html = clean_html_for_llm(html_content)

    prompt = f"""
You are an Expert Product Extraction Agent.

Your job is to parse the HTML of a product detail page and extract fields according to the schema.

Product URL:
{product_url}

Extract as many fields as possible:
- product name
- brand / manufacturer
- category hierarchy
- product URL
- description
- specifications / attributes
- image URLs
- alternative products
- product variants

For variants, extract:
- Stock Keeping Unit (SKU), item number, item code, product code, or catalog number if clearly visible
- size, color, pack, or unit
- price if publicly visible
- availability if publicly visible

Important SKU rules:
- Only extract SKU if it is clearly shown as SKU, item number, item code, product code, or catalog number.
- Do not use option indexes, product IDs, hidden form values, or values like 0 or 1 as SKU.
- If SKU is not visible, return null.

General rules:
- If a field is not visible, return null or an empty list.
- Do not invent missing information.
- Keep product_url exactly as provided.

HTML Content:
{cleaned_html}
"""

    return client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=ProductModel,
        messages=[{"role": "user", "content": prompt}],
    )