#!/usr/bin/env python3
"""Day 3: Export structured data to Google Sheets."""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import re
import pandas as pd
from loguru import logger
from src.storage.database import get_connection
from src.output.sheets_uploader import get_client, ensure_sheet, ensure_tabs, upload_dataframe
from src.entity_resolution.resolver import EntityResolver
import config.settings as settings


URL_PATTERN = re.compile(r'^https?://[^\s/$.?#].[^\s]*$')


def validate_source_urls(df: pd.DataFrame, label: str) -> pd.DataFrame:
    if "source_url" not in df.columns:
        return df
    before = len(df)
    has_url = df["source_url"].notna() & df["source_url"].astype(str).str.match(URL_PATTERN)
    bad = df[~has_url]
    if len(bad) > 0:
        logger.warning(f"{label}: {len(bad)} records with missing/invalid source URLs dropped")
        df = df[has_url]
    logger.info(f"{label}: {len(df)} records (dropped {before - len(df)} bad)")
    return df


def load_table_as_df(conn, table: str) -> pd.DataFrame:
    query = f"SELECT * FROM {table}"
    return pd.read_sql_query(query, conn)


def remap_startups(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["schemaVersion"] = df.get("schema_version", "1.0")
    out["recordType"] = "STARTUP"
    out["source.name"] = df.get("source_name", "Y Combinator")
    out["source.url"] = df.get("source_url")
    out["content.entityName"] = df.get("canonical_name").fillna("").combine_first(df.get("entity_name").fillna(""))
    out["content.data.description"] = df.get("description")
    out["content.data.foundedYear"] = df.get("founded_year")
    out["content.data.employeeCount"] = df.get("employee_count", 0).fillna(0).astype(int)
    out["content.data.location"] = df.get("location")
    out["content.data.website"] = df.get("website")
    out["content.data.fundingTotal"] = df.get("funding_total")
    out["collectedAt"] = df.get("collected_at")
    return out

def remap_products(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["schemaVersion"] = df.get("schema_version", "1.0")
    out["recordType"] = "PRODUCT"
    out["source.name"] = df.get("source_name", "Product Hunt")
    out["source.url"] = df.get("source_url")
    out["content.productName"] = df.get("product_name")
    out["content.startupName"] = df.get("canonical_company").fillna("").combine_first(df.get("startup_name").fillna(""))
    out["content.description"] = df.get("description")
    pricing = df.get("pricing_model")
    out["content.pricingModel"] = pricing.fillna("").apply(lambda x: x.upper() if x else "")
    out["content.website"] = df.get("website")
    out["content.category"] = df.get("category")
    out["collectedAt"] = df.get("collected_at")
    return out

def remap_papers(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["schemaVersion"] = df.get("schema_version", "1.0")
    out["recordType"] = "RESEARCH_PAPER"
    out["content.title"] = df.get("title")
    out["content.authors"] = df.get("authors")
    out["content.paper_url"] = df.get("paper_url")
    out["content.github_url"] = df.get("github_url")
    out["content.github_stars"] = df.get("github_stars", 0).fillna(0).astype(int)
    out["content.published_date"] = df.get("published_date")
    out["collectedAt"] = df.get("collected_at")
    return out

def remap_jobs(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["schemaVersion"] = df.get("schema_version", "1.0")
    out["recordType"] = "JOB"
    out["content.company"] = df.get("company")
    out["content.role_title"] = df.get("role_title")
    out["content.role_family"] = df.get("role_family")
    out["content.date"] = df.get("published_date")
    out["content.is_remote"] = df.get("is_remote", 0).fillna(0).astype(bool)
    out["content.location"] = df.get("location")
    out["content.salary_range"] = df.get("salary_range")
    out["collectedAt"] = df.get("collected_at")
    return out

def remap_news(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["schemaVersion"] = df.get("schema_version", "1.0")
    out["recordType"] = "NEWS"
    out["source.name"] = df.get("source_name")
    out["source.url"] = df.get("source_url")
    out["content.title"] = df.get("title")
    out["content.summary"] = df.get("summary")
    out["content.published_date"] = df.get("published_date")
    out["collectedAt"] = df.get("collected_at")
    return out


def main():
    logger.add(settings.LOG_PATH, rotation="10 MB")
    logger.info("=== EXPORT TO SHEETS STARTING ===")

    conn = get_connection(settings.STRUCTURED_DB_PATH)

    resolver = EntityResolver(threshold=settings.FUZZY_THRESHOLD)

    # Load and resolve
    df_startups_raw = load_table_as_df(conn, "startups")
    if not df_startups_raw.empty:
        df_startups_raw["canonical_name"] = df_startups_raw["entity_name"].apply(
            lambda x: resolver.resolve(str(x)) if pd.notna(x) else x
        )

    df_products_raw = load_table_as_df(conn, "products")
    if not df_products_raw.empty:
        df_products_raw["canonical_company"] = df_products_raw["startup_name"].apply(
            lambda x: resolver.resolve(str(x)) if pd.notna(x) else x
        )

    df_papers_raw = load_table_as_df(conn, "research_papers")
    df_jobs_raw = load_table_as_df(conn, "jobs")
    df_news_raw = load_table_as_df(conn, "news")

    # Validate source URLs (use source_url column from raw)
    logger.info("--- Validating source URLs (anti-hallucination check) ---")
    df_startups_raw = validate_source_urls(df_startups_raw, "Startups")
    df_products_raw = validate_source_urls(df_products_raw, "Products")
    df_papers_raw = validate_source_urls(df_papers_raw, "Research Papers")
    df_jobs_raw = validate_source_urls(df_jobs_raw, "Jobs")
    df_news_raw = validate_source_urls(df_news_raw, "News")

    # Remap to expected schema
    df_startups = remap_startups(df_startups_raw)
    df_products = remap_products(df_products_raw)
    df_papers = remap_papers(df_papers_raw)
    df_jobs = remap_jobs(df_jobs_raw)
    df_news = remap_news(df_news_raw)
    df_entity_log = pd.DataFrame(resolver.get_log())

    # Export to CSV
    export_dir = os.path.join(os.path.dirname(__file__), "..", "data", "exports")
    os.makedirs(export_dir, exist_ok=True)

    csv_files = {
        "Startups.csv": df_startups,
        "Products.csv": df_products,
        "Research Papers.csv": df_papers,
        "Jobs.csv": df_jobs,
        "News.csv": df_news,
        "Entity Mapping Log.csv": df_entity_log,
    }
    for filename, df in csv_files.items():
        path = os.path.join(export_dir, filename)
        df.to_csv(path, index=False)
        logger.info(f"Saved {len(df)} rows to {path}")

    # Try Google Sheets upload
    try:
        gc = get_client()
        sh = ensure_sheet(gc)
        ensure_tabs(sh, settings.TABS)

        upload_dataframe(sh, "Startups", df_startups)
        upload_dataframe(sh, "Products", df_products)
        upload_dataframe(sh, "Research Papers", df_papers)
        upload_dataframe(sh, "Jobs", df_jobs)
        upload_dataframe(sh, "News", df_news)
        upload_dataframe(sh, "Entity Mapping Log", df_entity_log)
        logger.info("=== GOOGLE SHEETS EXPORT COMPLETE ===")
    except Exception as e:
        logger.warning(f"Google Sheets upload failed: {e}")
        logger.info("CSV files saved to data/exports/ — import them manually to Google Sheets")

    conn.close()
    logger.info("=== EXPORT COMPLETE ===")


if __name__ == "__main__":
    main()
