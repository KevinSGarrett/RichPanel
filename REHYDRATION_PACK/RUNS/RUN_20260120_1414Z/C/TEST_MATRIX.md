# Test Matrix (Agent C)

| Test | Command | Result | Notes |
| --- | --- | --- | --- |
| Eval script unit tests | `python scripts/test_eval_order_status_intent.py` | PASS | Output structure + baseline score checks. |
| Richpanel client unit tests | `python scripts/test_richpanel_client.py` | PASS | Includes read-only guard coverage. |
| CI checks | `python scripts/run_ci_checks.py --ci` | FAIL | Fails when git status is non-empty (generated docs + new run artifacts). |
