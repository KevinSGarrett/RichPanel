# B74/C Evidence

## AWS Account Identity (prod)
Command:
```
aws sts get-caller-identity
```
Output:
```
{
  "UserId": "AROA4Y5MQEN3E5KRSFG44:rp-deployer-prod",
  "Account": "878145708918",
  "Arn": "arn:aws:sts::878145708918:assumed-role/AWSReservedSSO_RP-Deployer_19cf80c2655853f2/rp-deployer-prod"
}
```

## Canary Artifacts (PII-safe)
- `REHYDRATION_PACK/RUNS/B74/C/PROOF/prod_shadow_canary_200.json`
- `REHYDRATION_PACK/RUNS/B74/C/PROOF/prod_shadow_canary_200.md`

## Canary Summary Snippet
```
Run ID: RUN_20260209_1928Z
Tickets scanned: 200
Global order-status rate: 42.0%
Match rate among order-status: 98.8%
Tracking present rate (matched only): 90.4%
ETA available rate (matched only): 7.2%
Richpanel 429 retries: 0
```

## Regression Guard Tests
```
python -m pytest backend/tests/test_order_status_regression_guard.py
```
Result:
```
2 passed in 0.24s
```
