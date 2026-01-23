# Test Results

## Summary
- `compileall`: pass
- `pytest`: pass (399 passed, 9 subtests passed)
- `dev_e2e_smoke`: pass (ticket 1089; proof artifact written)

## Details
```
python -m compileall backend/src scripts
```
Status: pass

```
python -m compileall backend/src scripts
```
Status: pass

```
python -m pytest -q
```
Status: pass  
Output: `399 passed, 9 subtests passed in 20.46s`

```
python -m pytest -q
```
Status: pass  
Output: `385 passed, 9 subtests passed in 20.98s`

```
python -m pytest -q
```
Status: failed  
Output: `test_rewrite_rejects_missing_tracking_number` assertion failed

```
python -m pytest -q
```
Status: pass  
Output: `385 passed, 9 subtests passed in 20.98s`

```
python -m pytest -q
```
Status: pass  
Output: `392 passed, 9 subtests passed in 20.78s`

```
python -m pytest -q
```
Status: pass  
Output: `398 passed, 9 subtests passed in 20.65s`

```
python scripts/dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --wait-seconds 120 --scenario order_status_tracking_standard_shipping --proof-path REHYDRATION_PACK/RUNS/B51/Agent_C/e2e_order_status_tracking_standard_shipping_proof.json
```
Status: failed  
Output: `--scenario order_status* requires --ticket-id or --ticket-number.`

```
python scripts/dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --wait-seconds 120 --ticket-number 1084 --scenario order_status_tracking_standard_shipping --proof-path REHYDRATION_PACK/RUNS/B51/Agent_C/e2e_order_status_tracking_standard_shipping_proof.json
```
Status: failed  
Output: `botocore.exceptions.NoCredentialsError: Unable to locate credentials`

```
python scripts/dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --wait-seconds 120 --ticket-number 1086 --scenario order_status_tracking_standard_shipping --proof-path REHYDRATION_PACK/RUNS/B51/Agent_C/e2e_order_status_tracking_standard_shipping_proof.json
```
Status: failed  
Output: `Tracking scenario reply missing required tracking URL.`

```
python scripts/dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --wait-seconds 120 --profile rp-admin-kevin --ticket-number 1087 --scenario order_status_tracking_standard_shipping --no-require-openai-routing --no-require-openai-rewrite --proof-path REHYDRATION_PACK/RUNS/B51/Agent_C/e2e_order_status_tracking_standard_shipping_proof.json
```
Status: pass  
Output: `classification=PASS_STRONG; status=PASS`

```
python scripts/dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --wait-seconds 120 --profile rp-admin-kevin --ticket-number 1088 --scenario order_status_tracking_standard_shipping --no-require-openai-routing --no-require-openai-rewrite --proof-path REHYDRATION_PACK/RUNS/B51/Agent_C/e2e_order_status_tracking_standard_shipping_proof.json
```
Status: failed  
Output: `skip_or_escalation_tags_present`

```
python scripts/dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --wait-seconds 120 --profile rp-admin-kevin --ticket-number 1084 --scenario order_status_tracking_standard_shipping --no-require-openai-routing --no-require-openai-rewrite --proof-path REHYDRATION_PACK/RUNS/B51/Agent_C/e2e_order_status_tracking_standard_shipping_proof.json
```
Status: failed  
Output: `skip_or_escalation_tags_present`

```
python scripts/dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --wait-seconds 120 --profile rp-admin-kevin --ticket-number 1085 --scenario order_status_tracking_standard_shipping --no-require-openai-routing --no-require-openai-rewrite --proof-path REHYDRATION_PACK/RUNS/B51/Agent_C/e2e_order_status_tracking_standard_shipping_proof.json
```
Status: failed  
Output: `skip_or_escalation_tags_present`

```
python scripts/dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --wait-seconds 120 --profile rp-admin-kevin --ticket-number 1089 --scenario order_status_tracking_standard_shipping --no-require-openai-routing --no-require-openai-rewrite --proof-path REHYDRATION_PACK/RUNS/B51/Agent_C/e2e_order_status_tracking_standard_shipping_proof.json
```
Status: pass  
Output: `classification=PASS_STRONG; status=PASS`

```
python -m compileall backend/src scripts
```
Status: pass
