# Test Matrix — RUN_20260117_0212Z (Agent C)

| Scope | Command | Result |
| --- | --- | --- |
| Full CI-equivalent | `python scripts/run_ci_checks.py --ci` | ✅ PASS (clean tree) |
| Worker wiring | `python scripts/test_worker_handler_flag_wiring.py` | ✅ Included in CI suite |
| Richpanel client write guard | `python scripts/test_richpanel_client.py` | ✅ Included in CI suite |
| Read-only shadow pipeline | `python scripts/test_read_only_shadow_mode.py` | ✅ Included in CI suite |
| Pipeline handlers | `python scripts/test_pipeline_handlers.py` | ✅ Included in CI suite |
| OpenAI client offline | `python scripts/test_openai_client.py` | ✅ Included in CI suite |
| Shopify client offline | `python scripts/test_shopify_client.py` | ✅ Included in CI suite |
| ShipStation client offline | `python scripts/test_shipstation_client.py` | ✅ Included in CI suite |
| Order lookup offline | `python scripts/test_order_lookup.py` | ✅ Included in CI suite |
| Protected deletes | `python scripts/check_protected_deletes.py --ci` | ✅ Included in CI suite |
