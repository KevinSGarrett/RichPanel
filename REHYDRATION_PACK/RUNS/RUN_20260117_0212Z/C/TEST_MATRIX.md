# Test Matrix — RUN_20260117_0212Z

| Scope | Command | Result |
| --- | --- | --- |
| Full CI-equivalent | `python scripts/run_ci_checks.py --ci` | ✅ PASS (clean tree after regen) |
| Worker wiring | `python scripts/test_worker_handler_flag_wiring.py` | ✅ Included in CI suite |
| Richpanel client write guard | `python scripts/test_richpanel_client.py` | ✅ Included in CI suite |
| Read-only shadow pipeline | `python scripts/test_read_only_shadow_mode.py` | ✅ Included in CI suite |
