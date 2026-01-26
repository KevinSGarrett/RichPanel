# Changes — B59/A

- `backend/src/richpanel_middleware/integrations/richpanel/client.py`
  - Added prod-only write acknowledgment gating (`MW_PROD_WRITES_ACK`) for non-GET/HEAD calls.
  - Included `ENV` in environment resolution for prod detection.
- `backend/src/integrations/shopify/client.py`
  - Added prod-only write acknowledgment gating for non-GET/HEAD calls.
  - Included `ENV` in environment resolution for prod detection.
- `scripts/test_richpanel_client.py`
  - Added prod ack blocked/allowed tests plus non-prod regression coverage.
- `scripts/test_shopify_client.py`
  - Added prod ack blocked/allowed tests plus non-prod regression coverage.
- `docs/08_Engineering/Prod_ReadOnly_Shadow_Mode_Runbook.md`
  - Documented the two-man rule, required env var, and interlocks.
