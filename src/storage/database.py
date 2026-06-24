import sqlite3
import json
from datetime import datetime

def get_connection(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_raw_db(db_path: str = "data/raw.db"):
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            html TEXT,
            scraped_at TEXT NOT NULL,
            status INTEGER,
            source_type TEXT
        )
    """)
    conn.commit()
    conn.close()

def init_structured_db(db_path: str = "data/structured.db"):
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS startups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_url TEXT NOT NULL UNIQUE,
            source_name TEXT DEFAULT 'Y Combinator',
            record_type TEXT DEFAULT 'STARTUP',
            entity_name TEXT,
            canonical_name TEXT,
            description TEXT,
            founded_year INTEGER,
            employee_count INTEGER,
            location TEXT,
            website TEXT,
            funding_total TEXT,
            collected_at TEXT NOT NULL,
            schema_version TEXT DEFAULT '1.0'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_url TEXT NOT NULL UNIQUE,
            source_name TEXT DEFAULT 'Product Hunt',
            record_type TEXT DEFAULT 'PRODUCT',
            product_name TEXT,
            startup_name TEXT,
            canonical_company TEXT,
            description TEXT,
            pricing_model TEXT,
            website TEXT,
            category TEXT,
            collected_at TEXT NOT NULL,
            schema_version TEXT DEFAULT '1.0'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS research_papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_url TEXT NOT NULL UNIQUE,
            source_name TEXT DEFAULT 'ArXiv',
            record_type TEXT DEFAULT 'RESEARCH_PAPER',
            title TEXT NOT NULL,
            authors TEXT,
            paper_url TEXT,
            github_url TEXT,
            github_stars INTEGER,
            published_date TEXT,
            collected_at TEXT NOT NULL,
            schema_version TEXT DEFAULT '1.0'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_url TEXT NOT NULL,
            source_name TEXT DEFAULT 'RemoteOK',
            record_type TEXT DEFAULT 'JOB',
            company TEXT,
            canonical_company TEXT,
            role_title TEXT,
            role_family TEXT,
            published_date TEXT,
            is_remote INTEGER,
            location TEXT,
            salary_range TEXT,
            collected_at TEXT NOT NULL,
            schema_version TEXT DEFAULT '1.0',
            UNIQUE(source_url)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_url TEXT UNIQUE NOT NULL,
            source_name TEXT,
            record_type TEXT DEFAULT 'NEWS',
            title TEXT,
            summary TEXT,
            published_date TEXT,
            collected_at TEXT NOT NULL,
            schema_version TEXT DEFAULT '1.0'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entity_mapping_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_name TEXT,
            normalized_name TEXT,
            canonical_name TEXT,
            confidence REAL,
            resolved_at TEXT
        )
    """)

    conn.commit()
    conn.close()

def save_raw_page(conn, url: str, html: str | None, status: int, source_type: str):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO raw_pages (url, html, scraped_at, status, source_type)
        VALUES (?, ?, ?, ?, ?)
    """, (url, html, datetime.utcnow().isoformat(), status, source_type))
    conn.commit()

def url_exists(conn, url: str) -> bool:
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM raw_pages WHERE url = ?", (url,))
    return cursor.fetchone() is not None

def insert_startup(conn, record: dict):
    c = record["content"]
    d = c["data"]
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO startups (source_url, source_name, record_type, entity_name, description, founded_year, employee_count, location, website, funding_total, collected_at, schema_version)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        record.get("source", {}).get("url"),
        record.get("source", {}).get("name", "Y Combinator"),
        record.get("recordType", "STARTUP"),
        c.get("entityName"),
        d.get("description"),
        d.get("foundedYear"),
        d.get("employeeCount"),
        d.get("location"),
        d.get("website"),
        d.get("fundingTotal"),
        record.get("collectedAt"),
        record.get("schemaVersion", "1.0"),
    ))
    conn.commit()

def insert_product(conn, record: dict):
    c = record["content"]
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO products (source_url, source_name, record_type, product_name, startup_name, description, pricing_model, website, category, collected_at, schema_version)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        record.get("source", {}).get("url"),
        record.get("source", {}).get("name", "Product Hunt"),
        record.get("recordType", "PRODUCT"),
        c.get("productName"),
        c.get("startupName"),
        c.get("description"),
        c.get("pricingModel"),
        c.get("website"),
        c.get("category"),
        record.get("collectedAt"),
        record.get("schemaVersion", "1.0"),
    ))
    conn.commit()

def insert_paper(conn, record: dict):
    c = record["content"]
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO research_papers (source_url, source_name, record_type, title, authors, paper_url, github_url, github_stars, published_date, collected_at, schema_version)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        record.get("source", {}).get("url"),
        record.get("source", {}).get("name", "ArXiv"),
        record.get("recordType", "RESEARCH_PAPER"),
        c.get("title"),
        json.dumps(c.get("authors")),
        c.get("paper_url"),
        c.get("github_url"),
        c.get("github_stars"),
        c.get("published_date"),
        record.get("collectedAt"),
        record.get("schemaVersion", "1.0"),
    ))
    conn.commit()

def insert_job(conn, record: dict):
    c = record["content"]
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO jobs (source_url, source_name, record_type, company, role_title, role_family, published_date, is_remote, location, salary_range, collected_at, schema_version)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        record.get("source", {}).get("url"),
        record.get("source", {}).get("name", "RemoteOK"),
        record.get("recordType", "JOB"),
        c.get("company"),
        c.get("role_title"),
        c.get("role_family"),
        c.get("date"),
        1 if c.get("is_remote") else 0,
        c.get("location"),
        c.get("salary_range"),
        record.get("collectedAt"),
        record.get("schemaVersion", "1.0"),
    ))
    conn.commit()

def insert_news(conn, record: dict):
    c = record["content"]
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO news (source_url, source_name, record_type, title, summary, published_date, collected_at, schema_version)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        record.get("source", {}).get("url"),
        record.get("source", {}).get("name", c.get("source_name")),
        record.get("recordType", "NEWS"),
        c.get("title"),
        c.get("summary"),
        c.get("published_date"),
        record.get("collectedAt"),
        record.get("schemaVersion", "1.0"),
    ))
    conn.commit()
