## B68 A — Changes

### Code
- Added email-channel enforcement and proof fields in `scripts/dev_e2e_smoke.py` (`--require-email-channel`, outbound endpoint, latest comment source).
- Added email outbound regression assertion in `scripts/test_pipeline_handlers.py`.
- Expanded E2E smoke unit tests in `scripts/test_e2e_smoke_encoding.py`.

### Docs
- Clarified Shopify live read-only usage and removed sandbox/dev store assumptions in:
  - `docs/08_Engineering/Secrets_and_Environments.md`
  - `docs/08_Testing_Quality/Order_Status_Sandbox_E2E_Suite.md`
  - `docs/09_Deployment_Operations/Environments.md`
  - `docs/00_Project_Admin/Open_Questions.md`
