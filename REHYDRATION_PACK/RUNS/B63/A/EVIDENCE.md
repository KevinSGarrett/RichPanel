# Evidence — B63/A

## Scope and safety
- Sandbox/dev only; no production writes.
- Outbound replies limited to allowlisted sandbox inboxes.
- Shopify order number fetched via read-only GET requests; stored only as hashed fingerprints in proofs.
- Proof artifacts are PII-safe (redaction + `dev_e2e_smoke.py` PII guard).

## Scenario commands (one-command harness)
### Golden path
```powershell
cd C:\RichPanel_GIT
python scripts/b63_sandbox_scenarios.py --scenario golden_path --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --profile rp-admin-kevin --order-number <redacted> --ticket-number <redacted>
```

### Non-order-status
```powershell
cd C:\RichPanel_GIT
python scripts/b63_sandbox_scenarios.py --scenario non_order_status --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --profile rp-admin-kevin
```

### Order-status no-match
```powershell
cd C:\RichPanel_GIT
python scripts/b63_sandbox_scenarios.py --scenario order_status_no_match --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --profile rp-admin-kevin --ticket-number <redacted>
```

### Order-status order-number
```powershell
cd C:\RichPanel_GIT
python scripts/b63_sandbox_scenarios.py --scenario order_status_order_number --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --profile rp-admin-kevin --order-number <redacted> --ticket-number <redacted> --wait-seconds 120
```

## Proof artifacts
- `REHYDRATION_PACK/RUNS/B63/A/PROOF/sandbox_golden_path_proof.json`
- `REHYDRATION_PACK/RUNS/B63/A/PROOF/sandbox_non_order_status_proof.json`
- `REHYDRATION_PACK/RUNS/B63/A/PROOF/sandbox_order_status_no_match_proof.json`
- `REHYDRATION_PACK/RUNS/B63/A/PROOF/sandbox_order_status_order_number_proof.json`

## CI
```powershell
cd C:\RichPanel_GIT
python scripts/run_ci_checks.py
```

```text
Ran 190 tests in 0.039s

OK
[OK] CI-equivalent checks passed.
```
