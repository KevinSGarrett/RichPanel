from __future__ import annotations

import sys
from typing import Optional

try:
    import boto3  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    boto3 = None  # type: ignore


def _load_aws_account_id() -> Optional[str]:
    if boto3 is None:
        return None
    try:
        return boto3.client("sts").get_caller_identity().get("Account")
    except Exception:
        return None


def main() -> int:
    account_id = _load_aws_account_id()
    print(f"Account={account_id or 'unknown'}")
    from shopify_health_check import main as _health_main  # noqa: WPS433

    return _health_main()


if __name__ == "__main__":
    raise SystemExit(main())
