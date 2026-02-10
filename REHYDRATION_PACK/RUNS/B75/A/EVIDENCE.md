# B75/A Evidence

## AWS Account Verification (dev)
Command:
```
aws sts get-caller-identity --profile rp-admin-dev
```
Output:
```
{
  "UserId": "AROA...:rp-admin-kevin",
  "Account": "151124909266",
  "Arn": "arn:aws:sts::151124909266:assumed-role/AWSReservedSSO_RP-Admin_65ba0b62bcc9f8ed/rp-admin-kevin"
}
```

## Secrets Preflight (dev)
Artifact:
- `REHYDRATION_PACK/RUNS/B75/A/PROOF/secrets_preflight_dev.json`
Summary: `overall_status=PASS` (no secret values printed).

## Unit Tests
Command:
```
python scripts/test_delivery_estimate.py
```
Result (summary):
```
Ran 27 tests in 0.008s
OK
```

Additional coverage:
```
python -m pytest backend/tests/test_tracking_link_generation.py
```
Result (summary):
```
8 passed in 0.15s
```

## Tracking URL Proof (redacted)
Artifact:
- `REHYDRATION_PACK/RUNS/B75/A/PROOF/tracking_url_unit_proof.json`

Notes:
- No raw emails, names, order numbers, or tracking numbers included.
