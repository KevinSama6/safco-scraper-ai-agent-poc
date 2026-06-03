import os
import pymysql
import json
from dotenv import load_dotenv
from models import ProductModel


load_dotenv()


# MySQL database configuration.
# Values are loaded from the .env file when available.
DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE", "safco_scraper"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}


def get_connection():
    
    # Create a MySQL connection with autocommit enabled.
   
    return pymysql.connect(**DB_CONFIG, autocommit=True)


def init_db():
    
    # Initialize the MySQL database and required tables.
    # Connect without selecting a database first, so the database can be created if needed.
    temp_config = DB_CONFIG.copy()
    db_name = temp_config.pop("database")

    conn = pymysql.connect(**temp_config, autocommit=True)
    cursor = conn.cursor()

    cursor.execute(
        f"""
        CREATE DATABASE IF NOT EXISTS {db_name}
        CHARACTER SET utf8mb4
        COLLATE utf8mb4_unicode_ci
        """
    )

    cursor.close()
    conn.close()

    # Connect to the target database and create tables.
    conn = get_connection()
    cursor = conn.cursor()

    # URL queue table.
    # This table supports checkpointing, resumability, and deduplication.
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS urls_queue (
            url VARCHAR(765) PRIMARY KEY,
            url_type VARCHAR(50),
            status VARCHAR(50),
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """
    )

    # Product data table.
    # The extracted structured product payload is stored as JSON text.
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            product_url VARCHAR(765) PRIMARY KEY,
            data LONGTEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """
    )

    cursor.close()
    conn.close()

    print("[DB] MySQL tables initialized successfully.")


def insert_url(url, url_type):

    # Insert a URL into the queue.

    # INSERT IGNORE prevents duplicate URLs from being inserted.

    conn = get_connection()
    cursor = conn.cursor()

    try:
        sql = """
            INSERT IGNORE INTO urls_queue (url, url_type, status)
            VALUES (%s, %s, 'pending')
        """
        cursor.execute(sql, (url, url_type))

    finally:
        cursor.close()
        conn.close()


def get_next_pending_url(url_type):

    # Fetch the next pending URL by URL type.
    # url_type can be 'category' or 'product'.

    conn = get_connection()
    cursor = conn.cursor()

    try:
        sql = """
            SELECT url
            FROM urls_queue
            WHERE url_type = %s AND status = 'pending'
            LIMIT 1
        """
        cursor.execute(sql, (url_type,))
        row = cursor.fetchone()

        return row["url"] if row else None

    finally:
        cursor.close()
        conn.close()


def update_url_status(url, status):
    
    # Update the processing status of a URL.

    conn = get_connection()
    cursor = conn.cursor()

    try:
        sql = """
            UPDATE urls_queue
            SET status = %s
            WHERE url = %s
        """
        cursor.execute(sql, (status, url))

    finally:
        cursor.close()
        conn.close()


def save_product(product: ProductModel):
   
    # Save extracted product data into MySQL.
    # ON DUPLICATE KEY UPDATE makes the write idempotent.
    # If the product URL already exists, the existing record will be updated.
    
    conn = get_connection()
    cursor = conn.cursor()

    try:
        sql = """
            INSERT INTO products (product_url, data)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE data = VALUES(data)
        """

        product_data = json.dumps(
            product.model_dump(),
            ensure_ascii=False
        )

        cursor.execute(sql, (product.product_url, product_data))

    finally:
        cursor.close()
        conn.close()