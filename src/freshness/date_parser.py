from datetime import datetime, timezone, timedelta
from dateutil import parser as dateparser
import re
from loguru import logger


def parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None

    date_str = date_str.strip()
    now = datetime.now(timezone.utc)

    relative_patterns = [
        (r'(\d+)\s*minute[s]?\s*ago', 'minutes'),
        (r'(\d+)\s*hour[s]?\s*ago', 'hours'),
        (r'(\d+)\s*day[s]?\s*ago', 'days'),
        (r'(\d+)\s*week[s]?\s*ago', 'weeks'),
        (r'just now', 'now'),
        (r'an? hour ago', 'one_hour'),
        (r'yesterday', 'yesterday'),
    ]

    for pattern, unit in relative_patterns:
        match = re.search(pattern, date_str, re.IGNORECASE)
        if match:
            if unit == 'now':
                return now
            elif unit == 'one_hour':
                return now - timedelta(hours=1)
            elif unit == 'yesterday':
                return now - timedelta(days=1)
            else:
                n = int(match.group(1))
                return now - timedelta(**{unit: n})

    try:
        dt = dateparser.parse(date_str)
        if dt:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
    except Exception as e:
        logger.warning(f"Date parse failed for '{date_str}': {e}")

    return None


def is_within_24_hours(dt: datetime | None) -> bool:
    if not dt:
        return False

    now = datetime.now(timezone.utc)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return (now - dt).total_seconds() < 86400


def extract_date_from_html(soup) -> datetime | None:
    meta_selectors = [
        ('meta', {'property': 'article:published_time'}),
        ('meta', {'name': 'date'}),
        ('meta', {'name': 'pubdate'}),
        ('meta', {'itemprop': 'datePublished'}),
        ('time', {'itemprop': 'datePublished'}),
        ('time', {'class': re.compile(r'date|time|publish', re.I)}),
    ]

    for tag, attrs in meta_selectors:
        el = soup.find(tag, attrs)
        if el:
            val = el.get('content') or el.get('datetime') or el.text
            if val:
                dt = parse_date(val)
                if dt:
                    return dt

    date_pattern = re.compile(
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}\b|'
        r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b|'
        r'\b\d{4}-\d{2}-\d{2}\b',
        re.IGNORECASE
    )

    text = soup.get_text()
    matches = date_pattern.findall(text)

    for match in matches[:3]:
        dt = parse_date(match)
        if dt:
            return dt

    return None
