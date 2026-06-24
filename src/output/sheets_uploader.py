import os
import gspread
import pandas as pd
from loguru import logger
import config.settings as settings


def get_client():
    json_path = settings.GOOGLE_SERVICE_ACCOUNT_JSON
    if json_path:
        logger.info(f"Using service account JSON at: {json_path}")
        if not os.path.exists(json_path):
            logger.error(f"Service account JSON file not found at: {json_path}")
            raise FileNotFoundError(f"Service account JSON not found: {json_path}")
        gc = gspread.service_account(filename=json_path)
    else:
        logger.info("No service account JSON configured, using OAuth")
        gc = gspread.oauth()
    return gc


def ensure_sheet(gc, sheet_name: str = settings.SHEET_NAME):
    try:
        sh = gc.open(sheet_name)
    except gspread.SpreadsheetNotFound:
        sh = gc.create(sheet_name)
        logger.info(f"Created new sheet: {sheet_name}")
    return sh


def ensure_tabs(sh, tabs: list[str]):
    existing = [ws.title for ws in sh.worksheets()]
    for tab in tabs:
        if tab not in existing:
            sh.add_worksheet(title=tab, rows=1000, cols=20)
            logger.info(f"Created tab: {tab}")


def upload_dataframe(sh, tab_name: str, df: pd.DataFrame):
    ws = sh.worksheet(tab_name)
    ws.clear()
    ws.update([df.columns.values.tolist()] + df.values.tolist())
    logger.info(f"Uploaded {len(df)} rows to tab '{tab_name}'")
