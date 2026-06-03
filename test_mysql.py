import pymysql
from db import init_db

try:
    from db import DB_CONFIG
    print(f"Connecting to MySQL... User: {DB_CONFIG['user']}, Port: {DB_CONFIG['port']}")
    
    init_db()
    print("Success! MySQL connected and database 'safco_scraper' initialized.")

except Exception as e:
    print("Connection failed. Error details:")
    print(e)