## B68 A — Changes

### Code
- Honored email-channel enforcement even outside order-status defaults in `scripts/dev_e2e_smoke.py` (email outbound checks now apply when email proof flags are set).
- Added unit regression coverage for the email `/send-message` path in `backend/tests/test_order_status_send_message.py`.

### Docs
- Clarified Shopify live read-only guidance in `docs/08_Engineering/Secrets_and_Environments.md`.
- Noted that integration tests use stubs/read-only services (no Shopify sandbox) in `docs/08_Testing_Quality/Test_Strategy_and_Matrix.md`.
