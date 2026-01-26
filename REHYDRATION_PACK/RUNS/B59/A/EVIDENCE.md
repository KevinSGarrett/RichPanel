# Evidence — B59/A

## Unit tests
```powershell
cd C:\RichPanel_GIT
python scripts\test_richpanel_client.py
python scripts\test_shopify_client.py
python scripts\test_openai_client.py
```

Output:
```
Ran 17 tests in 0.002s
OK

Ran 13 tests in 0.002s
OK

Ran 14 tests in 0.001s
OK
```

## Dev/sandbox E2E
```powershell
cd C:\RichPanel_GIT
python scripts\dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --profile rp-admin-kevin --scenario baseline --no-require-outbound --no-require-openai-routing --no-require-openai-rewrite --run-id B59-DEV-20260126-1609Z --proof-path REHYDRATION_PACK\RUNS\B59\A\PROOF\dev_e2e_smoke_proof.json
```

Result:
```
[OK] Event observed in rp_mw_dev_idempotency.
[OK] Conversation state + audit records written.
[OK] Wrote proof artifact to REHYDRATION_PACK\RUNS\B59\A\PROOF\dev_e2e_smoke_proof.json
[RESULT] classification=PASS_STRONG; status=PASS; failure_reason=none
```

## Key diffs
- PR files: https://github.com/KevinSGarrett/RichPanel/pull/186/files
- Compare: https://github.com/KevinSGarrett/RichPanel/compare/main...run/B59-A
- `backend/src/richpanel_middleware/integrations/richpanel/client.py`
- `backend/src/integrations/shopify/client.py`
- `backend/src/integrations/common.py`
- `backend/src/richpanel_middleware/integrations/shopify/client.py`
- `backend/src/richpanel_middleware/integrations/shopify/__init__.py`
- `backend/src/integrations/openai/client.py`
- `scripts/test_richpanel_client.py`
- `scripts/test_shopify_client.py`
- `scripts/test_openai_client.py`
- `docs/08_Engineering/Prod_ReadOnly_Shadow_Mode_Runbook.md`
- `docs/08_Engineering/Secrets_and_Environments.md`
- `docs/03_Richpanel_Integration/Shopify_Integration_Skeleton.md`
- `docs/06_Security_Privacy_Compliance/Secrets_and_Key_Management.md`
- `docs/_generated/doc_registry.json`
- `docs/_generated/doc_registry.compact.json`
- `docs/_generated/doc_outline.json`
- `docs/_generated/heading_index.json`
- `docs/00_Project_Admin/To_Do/_generated/PLAN_CHECKLIST_EXTRACTED.md`
- `docs/00_Project_Admin/To_Do/_generated/PLAN_CHECKLIST_SUMMARY.md`
- `docs/00_Project_Admin/To_Do/_generated/plan_checklist.json`
