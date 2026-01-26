# Evidence — B58/C

## Command (exact)
```powershell
$py = @'
import base64
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

import boto3

REGION = "us-east-2"
SHOP_DOMAIN = "scentimen-t.myshopify.com"
API_VERSION = "2026-01"

PROD_PROFILE = "rp-admin-prod"
DEV_PROFILE = "rp-admin-dev"

RICHPANEL_SECRET_ID = "rp-mw/prod/richpanel/api_key"
SHOPIFY_SECRET_ID = "rp-mw/dev/shopify/admin_api_token"


def get_secret(profile: str, secret_id: str) -> str:
    session = boto3.Session(profile_name=profile, region_name=REGION)
    client = session.client("secretsmanager", region_name=REGION)
    resp = client.get_secret_value(SecretId=secret_id)
    secret_value = resp.get("SecretString")
    if secret_value is None and resp.get("SecretBinary") is not None:
        secret_value = base64.b64decode(resp["SecretBinary"]).decode("utf-8")
    if not secret_value:
        raise RuntimeError(f"Missing secret value for {secret_id}")
    return secret_value


def fetch_status(url: str, token: str) -> int:
    req = urllib.request.Request(
        url, method="GET", headers={"X-Shopify-Access-Token": token}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.getcode() or 0
    except urllib.error.HTTPError as exc:
        return exc.code
    except Exception:
        return -1


# Fetch secrets via respective profiles
prod_richpanel_key = get_secret(PROD_PROFILE, RICHPANEL_SECRET_ID)
dev_shopify_token = get_secret(DEV_PROFILE, SHOPIFY_SECRET_ID)

# Validate Shopify token against orders endpoint (non-PII)
orders_url = (
    f"https://{SHOP_DOMAIN}/admin/api/{API_VERSION}/orders.json?status=any&limit=1"
)
orders_status = fetch_status(orders_url, dev_shopify_token)
print(f"shopify_orders_status: {orders_status}")
if orders_status >= 400:
    raise SystemExit("Shopify token check failed; aborting eval")

# Run eval with overrides (do not print secrets)
repo_root = Path(r"C:\\RichPanel_GIT")
cmd = [
    sys.executable,
    str(repo_root / "scripts" / "live_readonly_shadow_eval.py"),
    "--ticket-id",
    "94875",
    "--ticket-id",
    "98378",
    "--ticket-id",
    "94874",
    "--ticket-id",
    "95608",
    "--ticket-id",
    "98245",
    "--ticket-id",
    "94872",
    "--ticket-id",
    "84723",
    "--ticket-id",
    "95614",
    "--ticket-id",
    "97493",
    "--ticket-id",
    "97034",
    "--ticket-id",
    "95618",
    "--ticket-id",
    "95693",
    "--ticket-id",
    "95620",
    "--ticket-id",
    "95515",
    "--ticket-id",
    "98371",
    "--ticket-id",
    "95622",
    "--ticket-id",
    "95624",
    "--shopify-probe",
]

env = os.environ.copy()
env.update(
    {
        "AWS_DEFAULT_REGION": REGION,
        "AWS_REGION": REGION,
        "RICHPANEL_ENV": "prod",
        "MW_ALLOW_NETWORK_READS": "true",
        "RICHPANEL_WRITE_DISABLED": "true",
        "RICHPANEL_OUTBOUND_ENABLED": "false",
        "SHOPIFY_OUTBOUND_ENABLED": "true",
        "SHOPIFY_WRITE_DISABLED": "true",
        "SHOPIFY_SHOP_DOMAIN": SHOP_DOMAIN,
        "RICHPANEL_API_KEY_OVERRIDE": prod_richpanel_key,
        "SHOPIFY_ACCESS_TOKEN_OVERRIDE": dev_shopify_token,
    }
)

result = subprocess.run(cmd, cwd=str(repo_root), env=env)
raise SystemExit(result.returncode)
'@

$path = Join-Path $env:TEMP "run_shadow_eval_with_overrides.py"
Set-Content -Path $path -Value $py
$env:AWS_DEFAULT_REGION = "us-east-2"
$env:AWS_REGION = "us-east-2"
python $path
Remove-Item $path
```

## Read-only flags used
- `RICHPANEL_ENV=prod`
- `MW_ALLOW_NETWORK_READS=true`
- `RICHPANEL_WRITE_DISABLED=true`
- `RICHPANEL_OUTBOUND_ENABLED=false`
- `SHOPIFY_OUTBOUND_ENABLED=true`
- `SHOPIFY_WRITE_DISABLED=true`
- `SHOPIFY_SHOP_DOMAIN=scentimen-t.myshopify.com`

Overrides (secrets, not logged):
- `RICHPANEL_API_KEY_OVERRIDE` from `rp-mw/prod/richpanel/api_key` (via `rp-admin-prod`)
- `SHOPIFY_ACCESS_TOKEN_OVERRIDE` from `rp-mw/dev/shopify/admin_api_token` (via `rp-admin-dev`)

## PII-safe success snippet
```json
"counts": {
  "tickets_requested": 17,
  "tickets_scanned": 17,
  "order_status_candidates": 1,
  "orders_matched": 16,
  "tracking_found": 11,
  "eta_available": 16,
  "errors": 0
},
"env_flags": {
  "MW_ALLOW_NETWORK_READS": "true",
  "RICHPANEL_WRITE_DISABLED": "true"
},
"http_trace_summary": {
  "total_requests": 196,
  "methods": {"GET": 196},
  "services": {"shopify": 21, "richpanel": 170, "shipstation": 5},
  "allowed_methods_only": true
}
```

## Safety proof

### Richpanel client read-only enforcement
```python
READ_ONLY_ENVIRONMENTS = {"prod", "production", "staging"}
```

```python
if (self.read_only or self._writes_disabled()) and method_upper not in {
    "GET",
    "HEAD",
}:
    self._logger.warning("richpanel.write_blocked", ...)
    raise RichpanelWriteDisabledError(
        "Richpanel writes are disabled; request blocked"
    )
```

### Script guardrails (outbound not required)
```python
REQUIRED_FLAGS = {
    "MW_ALLOW_NETWORK_READS": "true",
    "RICHPANEL_WRITE_DISABLED": "true",
}
```

### No non-GET methods attempted
- `http_trace_summary.allowed_methods_only` is `true` and the methods list contains only `GET` (see snippet above).
