# Agent A Run Log — B79

Run ID: RUN_20260213_0438Z
Date: 2026-02-12

Scope: Update preorder ETA logic to tag-based detection + 45-day ship rule.
Safety: No outbound writes; read-only development.

## Test Commands + Outputs (read-only envs set)

Env for all commands:
RICHPANEL_READ_ONLY=true
RICHPANEL_WRITE_DISABLED=true
RICHPANEL_OUTBOUND_ENABLED=false
SHOPIFY_WRITE_DISABLED=true

1) python -m unittest scripts.test_delivery_estimate
Output:
....Invalid transit window for key 'standard' in SHIPPING_METHOD_TRANSIT_MAP_JSON; skipping.
..Invalid transit window for key 'standard' in SHIPPING_METHOD_TRANSIT_MAP_JSON; skipping.
Invalid transit window for key 'ground' in SHIPPING_METHOD_TRANSIT_MAP_JSON; skipping.
SHIPPING_METHOD_TRANSIT_MAP_JSON contained no valid entries; using defaults.
.Invalid SHIPPING_METHOD_TRANSIT_MAP_JSON; using defaults. error=Expecting property name enclosed in double quotes: line 1 column 2 (char 1)
.Invalid SHIPPING_METHOD_TRANSIT_MAP_JSON; expected object. Using defaults.
.......Invalid transit window for key 'standard' in SHIPPING_METHOD_TRANSIT_MAP_JSON; skipping.
SHIPPING_METHOD_TRANSIT_MAP_JSON contained no valid entries; using defaults.
...................
----------------------------------------------------------------------
Ran 34 tests in 0.010s

OK

2) python -m unittest scripts.test_pipeline_handlers
Output:
...........worker.flag_load_failed
Traceback (most recent call last):
  File "C:\\RichPanel_GIT\\backend\\src\\lambda_handlers\\worker\\handler.py", line 532, in _load_kill_switches
    response = _ssm_client().get_parameters(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\\RichPanel_GIT\\scripts\\test_pipeline_handlers.py", line 678, in get_parameters
    raise RuntimeError("ssm read blocked")
RuntimeError: ssm read blocked
.......................................automation.order_status_reply.failed
Traceback (most recent call last):
  File "C:\\RichPanel_GIT\\backend\\src\\richpanel_middleware\\automation\\pipeline.py", line 1932, in execute_order_status_reply
    update_success = _apply_update_candidates(
                     ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\\RichPanel_GIT\\backend\\src\\richpanel_middleware\\automation\\pipeline.py", line 1711, in _apply_update_candidates
    reply_response = executor.execute(
                     ^^^^^^^^^^^^^^^^^
  File "C:\\RichPanel_GIT\\scripts\\test_pipeline_handlers.py", line 1800, in execute
    raise TransportError("simulated write failure")
richpanel_middleware.integrations.richpanel.client.TransportError: simulated write failure
......................................................WARNING: Unknown risk label 'risk:R9'; defaulting to claude-opus-4-5-20251101.
.....................shipstation.missing_credentials
.shopify.match_diagnostics
shopify.match_diagnostics
shopify.match_diagnostics
.....shopify.match_diagnostics
shopify.match_diagnostics
..shopify.match_diagnostics
.shopify.match_diagnostics
.shopify.match_diagnostics
........shipstation.missing_credentials
....shipstation.missing_credentials
.shipstation.missing_credentials
......shopify.match_diagnostics
shopify.match_diagnostics
................richpanel.write_blocked
...richpanel.write_blocked
richpanel.write_blocked
richpanel.write_blocked
richpanel.write_blocked
.richpanel.write_blocked
................................
----------------------------------------------------------------------
Ran 206 tests in 52.340s

OK

3) python -m unittest discover -s scripts -p "test_*.py"
Output (tail):
----------------------------------------------------------------------
Ran 1490 tests in 223.704s

OK

4) python -m pytest -q scripts/test_delivery_estimate.py
Output:
..................................                                       [100%]
34 passed in 0.22s

5) python -m pytest -q scripts/test_pipeline_handlers.py
Output:
........................................................................ [ 72%]
............................                                             [100%]
100 passed in 28.47s

6) python scripts/run_ci_checks.py --ci
Output (tail):
[FAIL] Generated files changed after regen. Commit the regenerated outputs.
Hint: run `python scripts/run_ci_checks.py` locally, commit, and push.

Uncommitted changes:
M backend/src/richpanel_middleware/automation/delivery_estimate.py
M backend/src/richpanel_middleware/automation/pipeline.py
M docs/00_Project_Admin/Progress_Log.md
M docs/_generated/doc_outline.json
M docs/_generated/doc_registry.compact.json
M docs/_generated/doc_registry.json
M docs/_generated/heading_index.json
M scripts/test_delivery_estimate.py
M scripts/test_order_status_send_message.py
M scripts/test_pipeline_handlers.py
M scripts/test_read_only_shadow_mode.py
?? REHYDRATION_PACK/RUNS/RUN_20260213_0438Z/

7) python scripts/run_ci_checks.py --ci (after commit)
Output (tail):
[OK] CI-equivalent checks passed.

Commit:
- B79: fix preorder ETA via tag + 45-day rule (commit 4e9c086)

## Test Commands + Outputs (tag normalization update)

Env for all commands:
RICHPANEL_READ_ONLY=true
RICHPANEL_WRITE_DISABLED=true
RICHPANEL_OUTBOUND_ENABLED=false
SHOPIFY_WRITE_DISABLED=true

1) python -m unittest scripts.test_delivery_estimate
Output:
....Invalid transit window for key 'standard' in SHIPPING_METHOD_TRANSIT_MAP_JSON; skipping.
..Invalid transit window for key 'standard' in SHIPPING_METHOD_TRANSIT_MAP_JSON; skipping.
Invalid transit window for key 'ground' in SHIPPING_METHOD_TRANSIT_MAP_JSON; skipping.
SHIPPING_METHOD_TRANSIT_MAP_JSON contained no valid entries; using defaults.
.Invalid SHIPPING_METHOD_TRANSIT_MAP_JSON; using defaults. error=Expecting property name enclosed in double quotes: line 1 column 2 (char 1)
.Invalid SHIPPING_METHOD_TRANSIT_MAP_JSON; expected object. Using defaults.
.......Invalid transit window for key 'standard' in SHIPPING_METHOD_TRANSIT_MAP_JSON; skipping.
SHIPPING_METHOD_TRANSIT_MAP_JSON contained no valid entries; using defaults.
...................
----------------------------------------------------------------------
Ran 34 tests in 0.010s

OK

2) python -m unittest scripts.test_pipeline_handlers
Output:
...........worker.flag_load_failed
Traceback (most recent call last):
  File "C:\\RichPanel_GIT\\backend\\src\\lambda_handlers\\worker\\handler.py", line 532, in _load_kill_switches
    response = _ssm_client().get_parameters(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\\RichPanel_GIT\\scripts\\test_pipeline_handlers.py", line 678, in get_parameters
    raise RuntimeError("ssm read blocked")
RuntimeError: ssm read blocked
.......................................automation.order_status_reply.failed
Traceback (most recent call last):
  File "C:\\RichPanel_GIT\\backend\\src\\richpanel_middleware\\automation\\pipeline.py", line 1932, in execute_order_status_reply
    update_success = _apply_update_candidates(
                     ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\\RichPanel_GIT\\backend\\src\\richpanel_middleware\\automation\\pipeline.py", line 1711, in _apply_update_candidates
    reply_response = executor.execute(
                     ^^^^^^^^^^^^^^^^^
  File "C:\\RichPanel_GIT\\scripts\\test_pipeline_handlers.py", line 1800, in execute
    raise TransportError("simulated write failure")
richpanel_middleware.integrations.richpanel.client.TransportError: simulated write failure
......................................................WARNING: Unknown risk label 'risk:R9'; defaulting to claude-opus-4-5-20251101.
.....................shipstation.missing_credentials
.shopify.match_diagnostics
shopify.match_diagnostics
shopify.match_diagnostics
.....shopify.match_diagnostics
shopify.match_diagnostics
..shopify.match_diagnostics
.shopify.match_diagnostics
.shopify.match_diagnostics
........shipstation.missing_credentials
....shipstation.missing_credentials
.shipstation.missing_credentials
......shopify.match_diagnostics
shopify.match_diagnostics
................richpanel.write_blocked
...richpanel.write_blocked
richpanel.write_blocked
richpanel.write_blocked
richpanel.write_blocked
.richpanel.write_blocked
................................
----------------------------------------------------------------------
Ran 206 tests in 36.425s

OK

3) python -m unittest discover -s scripts -p "test_*.py"
Output (tail):
----------------------------------------------------------------------
Ran 1490 tests in 223.308s

OK

4) python -m pytest -q scripts/test_delivery_estimate.py
Output:
..................................                                       [100%]
34 passed in 0.22s

5) python -m pytest -q scripts/test_pipeline_handlers.py
Output:
........................................................................ [ 72%]
............................                                             [100%]
100 passed in 28.45s

6) python scripts/run_ci_checks.py --ci
Output (tail):
[FAIL] Generated files changed after regen. Commit the regenerated outputs.
Hint: run `python scripts/run_ci_checks.py` locally, commit, and push.

Uncommitted changes:
M backend/src/richpanel_middleware/automation/delivery_estimate.py
M scripts/test_delivery_estimate.py
?? claude_gate_audit.json

7) python scripts/run_ci_checks.py --ci (after commit)
Output (tail):
[OK] CI-equivalent checks passed.

Commit:
- B79: normalize preorder tag whitespace (commit 5e5223f)
