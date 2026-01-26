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
- `backend/src/richpanel_middleware/integrations/richpanel/client.py`
- `backend/src/integrations/shopify/client.py`
- `scripts/test_richpanel_client.py`
- `scripts/test_shopify_client.py`
- `docs/08_Engineering/Prod_ReadOnly_Shadow_Mode_Runbook.md`
