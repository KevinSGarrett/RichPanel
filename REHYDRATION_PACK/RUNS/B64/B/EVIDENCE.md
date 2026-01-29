# Evidence - B64/B

## Scope and safety

- Dev-only run; no production writes.
- Sandbox email ticket created using allowlisted address; no customer contact outside sandbox.
- Proof artifacts are PII-safe (emails redacted, IDs hashed).

## AWS auth

```powershell
cd C:\RichPanel_GIT
aws sso login --profile rp-admin-kevin
```

## Unit tests (pytest)

```powershell
cd C:\RichPanel_GIT
python -m pytest -q 2>&1 | Tee-Object -FilePath REHYDRATION_PACK\RUNS\B64\B\PROOF\pytest_output.txt
```

- Output: `REHYDRATION_PACK/RUNS/B64/B/PROOF/pytest_output.txt`
- Result: `PASS` (1037 passed, 14 subtests passed)

## Lint (ruff)

```powershell
cd C:\RichPanel_GIT
ruff check . 2>&1 | Tee-Object -FilePath REHYDRATION_PACK\RUNS\B64\B\PROOF\ruff_output.txt
```

- Output: `REHYDRATION_PACK/RUNS/B64/B/PROOF/ruff_output.txt`
- Result: `PASS`

## Coverage (CI-equivalent unittest + coverage)

```powershell
cd C:\RichPanel_GIT
coverage run -m unittest discover -s scripts -p "test_*.py"
coverage report 2>&1 | Tee-Object -FilePath REHYDRATION_PACK\RUNS\B64\B\PROOF\coverage_report.txt
coverage xml
```

- Output: `REHYDRATION_PACK/RUNS/B64/B/PROOF/coverage_report.txt`
- Result: `PASS` (Total coverage: 93%)

## dev_e2e_smoke (OpenAI intent + rewrite proof)

```powershell
cd C:\RichPanel_GIT
python scripts\dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --scenario order_status_tracking --require-openai-routing --require-openai-rewrite --ticket-id api-scentimenttesting3300-7ed66dc1-f575-431d-bdf9-9748d639e19f --proof-path REHYDRATION_PACK\RUNS\B64\B\PROOF\openai_intent_rewrite_proof.json --run-id b64-20260129-b11 --wait-seconds 120 --profile rp-admin-kevin 2>&1 | Tee-Object -FilePath REHYDRATION_PACK\RUNS\B64\B\PROOF\dev_e2e_smoke_output.txt
```

- Output: `REHYDRATION_PACK/RUNS/B64/B/PROOF/dev_e2e_smoke_output.txt`
- Result: `PASS_STRONG`
- Proof JSON: `REHYDRATION_PACK/RUNS/B64/B/PROOF/openai_intent_rewrite_proof.json`
- OpenAI routing response id: `chatcmpl-D3Tjmr5Dn1ET5Sb9u28wEraHXGQN0`
- OpenAI rewrite response id: `chatcmpl-D3TjpufE3zqkMoXSESgNootEXg4th`

## Proof artifacts

- Created ticket artifact: `REHYDRATION_PACK/RUNS/B64/B/PROOF/created_ticket.json`
- Proof JSON: `REHYDRATION_PACK/RUNS/B64/B/PROOF/openai_intent_rewrite_proof.json`
