# B54-C Evidence — FINAL

## Primary Workflow Run (17 Tickets)
- **Workflow:** `.github/workflows/shadow_live_readonly_eval.yml`
- **Run ID:** 21324121333
- **Run URL:** https://github.com/KevinSGarrett/RichPanel/actions/runs/21324121333
- **Status:** ✅ SUCCESS
- **Timestamp:** 2026-01-25T00:33:24Z

### Dispatch Command
```bash
gh workflow run shadow_live_readonly_eval.yml \
  -f "ticket-ids=94875,98378,94874,95608,98245,94872,84723,95614,97493,97034,95618,95693,95620,95515,98371,95622,95624" \
  -f "shop-domain=scentimen-t.myshopify.com" \
  -f "shopify-probe=true" \
  --ref main
```

## Workflow Artifacts (RUN_20260125_0033Z)
- `artifacts/readonly_shadow/live_readonly_shadow_eval_report_RUN_20260125_0033Z.json`
- `artifacts/readonly_shadow/live_readonly_shadow_eval_report_RUN_20260125_0033Z.md`
- `artifacts/readonly_shadow/live_readonly_shadow_eval_http_trace_RUN_20260125_0033Z.json`

## Key Evidence Points

### 1. Read-Only Enforcement ✅
```json
"http_trace_summary": {
  "total_requests": 190,
  "methods": {"GET": 190},
  "services": {"richpanel": 170, "shopify": 20},
  "allowed_methods_only": true
}
```

### 2. Shopify Probe Success ✅
```json
"shopify_probe": {
  "enabled": true,
  "status_code": 200,
  "dry_run": false,
  "ok": true
}
```

### 3. Order Resolution Success ✅
- 16/17 tickets (94.1%) successfully resolved to Shopify orders
- Resolution strategies:
  - `richpanel_order_number`: 9 (high confidence)
  - `shopify_email_name`: 3 (high confidence)
  - `shopify_email_only`: 3 (high/medium confidence)
  - `richpanel_order_number_then_shopify_identity`: 2 (high confidence)

### 4. PII Safety ✅
```json
"notes": [
  "Ticket identifiers are hashed.",
  "No message bodies or customer identifiers are stored.",
  "HTTP trace captures urllib.request calls; AWS SDK calls are not included."
]
```

### 5. Environment Flags ✅
```json
"env_flags": {
  "MW_ALLOW_NETWORK_READS": "true",
  "RICHPANEL_OUTBOUND_ENABLED": "true",
  "RICHPANEL_WRITE_DISABLED": "true"
}
```

## PR Evidence
- **PR:** https://github.com/KevinSGarrett/RichPanel/pull/181
- **State:** MERGED
- **Merged at:** 2026-01-25T00:09:07Z
- **Labels:** `risk:R2`, `gate:claude`
- **PR body score:** 98/100

### CI/Codecov/Bugbot Status
| Check | Status |
|-------|--------|
| CI (validate) | ✅ SUCCESS |
| Codecov (patch) | ✅ 99.48% |
| Bugbot | ✅ Reviewed |
| Claude gate | ✅ PASS |
| Risk label | ✅ SUCCESS |

## Validation Checklist ✅
- [x] `counts.tickets_scanned` equals requested sample size (17)
- [x] `http_trace_summary.allowed_methods_only` is `true`
- [x] `shopify_probe.ok` is `true`
- [x] No customer identifiers, message bodies, or full order numbers in artifacts
- [x] Order resolution strategies functional (94.1% success rate)
- [x] No writes to Richpanel or Shopify (0 POST/PUT/PATCH/DELETE)
