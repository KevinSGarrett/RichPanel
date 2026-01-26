# Evidence — B59/A

## Unit tests
```powershell
cd C:\RichPanel_GIT
python scripts\test_richpanel_client.py
python scripts\test_shopify_client.py
```

Output:
```
Ran 17 tests in 0.002s
OK

Ran 12 tests in 0.003s
OK
```

## Key diffs
- PR files: https://github.com/KevinSGarrett/RichPanel/pull/186/files
- Compare: https://github.com/KevinSGarrett/RichPanel/compare/main...run/B59-A
- `backend/src/richpanel_middleware/integrations/richpanel/client.py`
- `backend/src/integrations/shopify/client.py`
- `backend/src/integrations/common.py`
- `scripts/test_richpanel_client.py`
- `scripts/test_shopify_client.py`
- `docs/08_Engineering/Prod_ReadOnly_Shadow_Mode_Runbook.md`
- `docs/08_Engineering/Secrets_and_Environments.md`
- `docs/03_Richpanel_Integration/Shopify_Integration_Skeleton.md`
- `docs/_generated/doc_registry.json`
- `docs/_generated/doc_registry.compact.json`
- `docs/_generated/doc_outline.json`
- `docs/_generated/heading_index.json`
- `docs/00_Project_Admin/To_Do/_generated/PLAN_CHECKLIST_EXTRACTED.md`
- `docs/00_Project_Admin/To_Do/_generated/PLAN_CHECKLIST_SUMMARY.md`
- `docs/00_Project_Admin/To_Do/_generated/plan_checklist.json`
