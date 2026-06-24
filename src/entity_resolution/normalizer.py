import re

SUFFIXES_TO_STRIP = [
    r'\binc\.?\b', r'\bllc\.?\b', r'\bltd\.?\b', r'\bcorp\.?\b',
    r'\bco\.?\b', r'\bpte\.?\b', r'\bplc\.?\b', r'\bgmbh\.?\b',
    r'\bsas\.?\b', r'\bab\.?\b', r'\bpbc\.?\b', r'\bllp\.?\b',
    r'\blp\.?\b', r'\bgmbh\s*&\s*co\.?\s*kg\.?\b',
]


def normalize_name(name: str) -> str:
    if not name:
        return ""

    n = name.lower().strip()

    for suffix in SUFFIXES_TO_STRIP:
        n = re.sub(suffix, '', n, flags=re.IGNORECASE)

    n = re.sub(r'[^\w\s-]', '', n)

    n = re.sub(r'\s+', ' ', n).strip()

    return n
