from __future__ import annotations

from shopify_health_check import _load_aws_account_id  # noqa: WPS433


def main() -> int:
    account_id = _load_aws_account_id()
    print(f"Account={account_id or 'unknown'}")
    from shopify_health_check import main as _health_main  # noqa: WPS433

    return _health_main()


if __name__ == "__main__":
    raise SystemExit(main())
