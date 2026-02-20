from __future__ import annotations

import re
from typing import List, Tuple

_MONTH_NAME_PATTERN = (
    r"January|February|March|April|May|June|July|August|September|October|November|December"
)
ETA_RANGE_REGEX = re.compile(
    r"\b(\d+)\s*(?:-|–|—|to)\s*(\d+)\s*(business\s+days?|bd|days?)\b",
    flags=re.IGNORECASE,
)
ETA_SINGLE_REGEX = re.compile(
    r"\b(\d+)\s*(business\s+days?|bd|days?)\b", flags=re.IGNORECASE
)
DATE_RANGE_SAME_YEAR_REGEX = re.compile(
    rf"\b(?:{_MONTH_NAME_PATTERN})\s+\d{{1,2}}\s*(?:–|—|-|to)\s*"
    rf"(?:{_MONTH_NAME_PATTERN})\s+\d{{1,2}},\s*\d{{4}}\b",
    flags=re.IGNORECASE,
)
DATE_RANGE_DIFFERENT_YEAR_REGEX = re.compile(
    rf"\b(?:{_MONTH_NAME_PATTERN})\s+\d{{1,2}},\s*\d{{4}}\s*(?:–|—|-|to)\s*"
    rf"(?:{_MONTH_NAME_PATTERN})\s+\d{{1,2}},\s*\d{{4}}\b",
    flags=re.IGNORECASE,
)


def dedupe(items: List[str]) -> List[str]:
    seen = set()
    deduped: List[str] = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def _normalize_eta_unit(unit: str) -> str:
    return re.sub(r"\s+", " ", unit.strip().lower())


def _normalize_date_window(token: str) -> str:
    normalized = token.strip().lower()
    normalized = re.sub(r"\s*(?:–|—|-)\s*", "-", normalized)
    normalized = re.sub(r"\s*\bto\b\s*", "-", normalized)
    normalized = re.sub(r"\s*,\s*", ", ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def extract_eta_windows_normalized(text: str) -> List[str]:
    if not text:
        return []
    windows: List[str] = []
    spans: List[Tuple[int, int]] = []
    for match in ETA_RANGE_REGEX.finditer(text):
        spans.append(match.span())
        min_days = match.group(1)
        max_days = match.group(2)
        unit = _normalize_eta_unit(match.group(3))
        windows.append(f"{min_days}-{max_days} {unit}")
    for match in ETA_SINGLE_REGEX.finditer(text):
        start, end = match.span()
        if any(start < span_end and end > span_start for span_start, span_end in spans):
            continue
        days = match.group(1)
        unit = _normalize_eta_unit(match.group(2))
        windows.append(f"{days} {unit}")
    return dedupe(windows)


def extract_date_windows_normalized(text: str) -> List[str]:
    if not text:
        return []
    windows: List[str] = []
    for match in DATE_RANGE_SAME_YEAR_REGEX.finditer(text):
        windows.append(_normalize_date_window(match.group(0)))
    for match in DATE_RANGE_DIFFERENT_YEAR_REGEX.finditer(text):
        windows.append(_normalize_date_window(match.group(0)))
    return dedupe(windows)


# Verbatim extractors preserve original dash/case for prompt injection,
# while normalized extractors collapse dash variants for validator matching.


def extract_eta_windows_verbatim(text: str) -> List[str]:
    if not text:
        return []
    windows: List[str] = []
    spans: List[Tuple[int, int]] = []
    for match in ETA_RANGE_REGEX.finditer(text):
        spans.append(match.span())
        windows.append(match.group(0).strip())
    for match in ETA_SINGLE_REGEX.finditer(text):
        start, end = match.span()
        if any(start < span_end and end > span_start for span_start, span_end in spans):
            continue
        windows.append(match.group(0).strip())
    return dedupe(windows)


def extract_date_windows_verbatim(text: str) -> List[str]:
    if not text:
        return []
    windows: List[str] = []
    for match in DATE_RANGE_SAME_YEAR_REGEX.finditer(text):
        windows.append(match.group(0).strip())
    for match in DATE_RANGE_DIFFERENT_YEAR_REGEX.finditer(text):
        windows.append(match.group(0).strip())
    return dedupe(windows)

