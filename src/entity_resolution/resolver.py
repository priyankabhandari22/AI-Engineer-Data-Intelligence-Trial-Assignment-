from rapidfuzz import fuzz, process
from .seed_entities import CANONICAL_COMPANIES
from .normalizer import normalize_name
import re


def _compact(s: str) -> str:
    return re.sub(r'[\s_-]+', '', s)


def _build_index(companies: list[str]) -> dict[str, str]:
    idx = {}
    for c in companies:
        n = normalize_name(c)
        idx[n] = c
        idx[_compact(n)] = c
    return idx


CANONICAL_INDEX = _build_index(CANONICAL_COMPANIES)


class EntityResolver:
    def __init__(self, threshold: int = 85):
        self.threshold = threshold
        self.canonical_map = {}
        self.resolution_log = []

    def resolve(self, raw_name: str) -> str:
        if not raw_name:
            return raw_name

        if raw_name in self.canonical_map:
            return self.canonical_map[raw_name]

        normalized = normalize_name(raw_name)
        compact = _compact(normalized)

        if compact in CANONICAL_INDEX:
            canonical = CANONICAL_INDEX[compact]
            match_score = 100
        elif normalized in CANONICAL_INDEX:
            canonical = CANONICAL_INDEX[normalized]
            match_score = 100
        else:
            match = process.extractOne(
                compact,
                [k for k in CANONICAL_INDEX.keys() if _compact(k) == k],
                scorer=fuzz.token_sort_ratio
            )
            if match and match[1] >= self.threshold:
                canonical = CANONICAL_INDEX[match[0]]
                match_score = match[1]
            else:
                canonical = raw_name
                match_score = None

        self.resolution_log.append({
            "raw_name": raw_name,
            "normalized": normalized,
            "canonical": canonical,
            "confidence": match_score,
            "resolved_at": None,
        })

        self.canonical_map[raw_name] = canonical
        return canonical

    def get_log(self) -> list[dict]:
        return self.resolution_log
