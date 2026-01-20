# Test Matrix (Agent C)

| Test | Command | Result | Notes |
| --- | --- | --- | --- |
| Eval script unit tests | `python scripts/test_eval_order_status_intent.py` | PASS | Output structure + baseline score checks. |
| Richpanel client unit tests | `python scripts/test_richpanel_client.py` | PASS | Includes read-only guard coverage. |
| Shadow eval tests | `python scripts/test_live_readonly_shadow_eval.py` | PASS | GET/HEAD trace validation covered. |
| CI checks | `python scripts/run_ci_checks.py --ci` | PASS | CI-equivalent checks passed (see RUN_REPORT snippet). |
