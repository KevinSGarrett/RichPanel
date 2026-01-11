#!/usr/bin/env python3
"""
verify_secret_inventory_sync.py

Offline drift-guard: fail CI if our documented canonical Secrets Manager IDs drift
from the code defaults that reference them.

Design goals:
- Standard library only
- Offline (no AWS calls)
- Deterministic + repo-relative
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable

REQUIRED_CANONICAL_SECRET_IDS: list[str] = [
    # Richpanel
    "rp-mw/<env>/richpanel/api_key",
    "rp-mw/<env>/richpanel/webhook_token",
    # OpenAI
    "rp-mw/<env>/openai/api_key",
    # Shopify
    "rp-mw/<env>/shopify/admin_api_token",
    # ShipStation
    "rp-mw/<env>/shipstation/api_key",
    "rp-mw/<env>/shipstation/api_secret",
    "rp-mw/<env>/shipstation/api_base",
]


DEFAULT_DOC_PATH = Path("docs/06_Security_Secrets/Access_and_Secrets_Inventory.md")
DEFAULT_CODE_DIRS = [
    Path("backend/src"),
    Path("infra/cdk/lib"),
]


_DOC_SECRET_RE = re.compile(r"rp-mw/<env>/[a-z0-9_/-]+", re.IGNORECASE)
_CODE_FSTRING_SECRET_RE = re.compile(r"rp-mw/\{[^}]+\}/[a-z0-9_/-]+", re.IGNORECASE)
_CODE_LITERAL_SECRET_RE = re.compile(
    r"rp-mw/(?:dev|staging|prod|local)/[a-z0-9_/-]+", re.IGNORECASE
)
_SECRET_PATH_CALL_RE = re.compile(r"\bsecretPath\s*\((?P<args>[^)]*)\)", re.IGNORECASE)
_STRING_LITERAL_RE = re.compile(r"""(["'])(?P<val>.*?)(?<!\\)\1""")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _normalize_secret_id(raw: str) -> str:
    value = raw.strip().strip("`").strip().strip('"').strip("'")
    value = value.lstrip("/")  # tolerate /rp-mw/... from copied SSM-style strings
    value = value.replace("\\", "/")
    value = value.strip()

    # Normalize any template env segment to <env>.
    value = re.sub(r"^rp-mw/\{[^}]+\}", "rp-mw/<env>", value, flags=re.IGNORECASE)
    value = re.sub(r"^rp-mw/\$\{[^}]+\}", "rp-mw/<env>", value, flags=re.IGNORECASE)

    return value.lower()


def extract_doc_secret_ids(doc_text: str) -> set[str]:
    found = {
        _normalize_secret_id(m.group(0)) for m in _DOC_SECRET_RE.finditer(doc_text)
    }
    return found


def _extract_secret_path_calls(text: str) -> set[str]:
    """
    Extract secrets referenced via MwNaming.secretPath("a", "b", ...) and normalize
    them to rp-mw/<env>/a/b/... for comparison against docs.
    """
    found: set[str] = set()
    for match in _SECRET_PATH_CALL_RE.finditer(text):
        args = match.group("args") or ""
        segments = [m.group("val") for m in _STRING_LITERAL_RE.finditer(args)]
        segments = [
            s.strip().strip("/").replace("\\", "/") for s in segments if s.strip()
        ]
        if not segments:
            continue
        found.add(_normalize_secret_id("rp-mw/<env>/" + "/".join(segments)))
    return found


def extract_code_secret_ids_from_text(text: str) -> set[str]:
    found: set[str] = set()

    for m in _CODE_FSTRING_SECRET_RE.finditer(text):
        found.add(_normalize_secret_id(m.group(0)))

    for m in _CODE_LITERAL_SECRET_RE.finditer(text):
        # Literal dev/staging/prod/local is normalized to <env> so docs can stay env-agnostic.
        literal = _normalize_secret_id(m.group(0))
        literal = re.sub(
            r"^rp-mw/(dev|staging|prod|local)/",
            "rp-mw/<env>/",
            literal,
            flags=re.IGNORECASE,
        )
        found.add(literal)

    found |= _extract_secret_path_calls(text)

    return found


def iter_code_files(root: Path, code_dirs: Iterable[Path]) -> Iterable[Path]:
    for rel_dir in code_dirs:
        abs_dir = (root / rel_dir).resolve()
        if not abs_dir.exists():
            continue
        for path in abs_dir.rglob("*"):
            if path.is_dir():
                continue
            if path.suffix.lower() not in {".py", ".ts"}:
                continue
            yield path


def extract_code_secret_ids(root: Path, code_dirs: Iterable[Path]) -> set[str]:
    found: set[str] = set()
    for path in iter_code_files(root, code_dirs):
        try:
            text = _read_text(path)
        except UnicodeDecodeError:
            continue
        found |= extract_code_secret_ids_from_text(text)
    return found


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Verify documented secret inventory matches code defaults (offline).")
    ap.add_argument(
        "--doc",
        default=str(DEFAULT_DOC_PATH),
        help="Path to Access_and_Secrets_Inventory.md (repo-relative).",
    )
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]

    doc_path = (root / args.doc).resolve()
    if not doc_path.exists():
        print(f"[FAIL] Inventory doc not found: {doc_path}")
        return 2

    doc_text = _read_text(doc_path)
    doc_secret_ids = extract_doc_secret_ids(doc_text)
    code_secret_ids = extract_code_secret_ids(root, DEFAULT_CODE_DIRS)

    required = [_normalize_secret_id(x) for x in REQUIRED_CANONICAL_SECRET_IDS]

    missing_in_doc = sorted([sid for sid in required if sid not in doc_secret_ids])
    missing_in_code = sorted([sid for sid in required if sid not in code_secret_ids])

    if missing_in_doc or missing_in_code:
        print("\n[FAIL] Secret inventory drift detected.")
        print(f"  Doc:  {doc_path.relative_to(root)}")
        print(f"  Code: {', '.join(str(p) for p in DEFAULT_CODE_DIRS)}")

        if missing_in_doc:
            print("\nMissing from inventory doc:")
            for sid in missing_in_doc:
                print(f"  - {sid}")

        if missing_in_code:
            print("\nMissing from code defaults:")
            for sid in missing_in_code:
                print(f"  - {sid}")

        print(
            "\nFix by updating the inventory doc and/or the integration default secret IDs."
        )
        return 1

    print("[OK] Secret inventory is in sync with code defaults.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
