# Agent B Notes - RUN_20260211_2118Z

## Commands

### python -m unittest scripts.test_order_lookup
```
Ran 113 tests in 50.278s

OK
```

### python -m unittest discover -s scripts -p "test_*.py"
```
ERROR: test_plan_actions_merges_ticket_snapshot_payload (test_pipeline_handlers.PipelineTests.test_plan_actions_merges_ticket_snapshot_payload)
...
botocore.exceptions.NoRegionError: You must specify a region.

Ran 1469 tests in 263.800s

FAILED (errors=1)
```

### python -m unittest discover -s scripts -p "test_*.py" (after AWS SSO login + us-east-2)
```
Ran 1469 tests in 215.752s

OK
```

### python -m pytest -q scripts/test_order_lookup.py
```
113 passed in 50.59s
```

### python scripts/run_ci_checks.py --ci (first run)
```
[FAIL] RUN_20260211_2118Z is NOT referenced in docs/00_Project_Admin/Progress_Log.md
```

### python scripts/run_ci_checks.py --ci (second run after progress log update)
```
[FAIL] Generated files changed after regen. Commit the regenerated outputs.
Uncommitted changes:
M backend/src/richpanel_middleware/commerce/order_lookup.py
M docs/00_Project_Admin/Progress_Log.md
M docs/_generated/doc_outline.json
M docs/_generated/doc_registry.compact.json
M docs/_generated/doc_registry.json
M docs/_generated/heading_index.json
M scripts/fixtures/order_lookup/shopify_order.json
M scripts/test_order_lookup.py
?? scripts/fixtures/order_lookup/shopify_order_gid.json
?? REHYDRATION_PACK/RUNS/RUN_20260211_2118Z/
?? .tmp.lambda_env.json
?? .tmp_pr_body_b76.md
?? .tmp_pr_body_b76_autogen.md
?? .tmp_required_checks.json
?? .tmp_required_checks_bugbot.json
?? .tmp_required_checks_restore.json
?? .tmp_required_checks_restore_again.json
?? REHYDRATION_PACK/RUNS/B75/B/PROOF/prod_ticket_116680_check.json
?? REHYDRATION_PACK/RUNS/B75/B/PROOF/prod_ticket_116680_check_after_botid_enable.json
?? REHYDRATION_PACK/RUNS/B75/B/PROOF/prod_ticket_116680_check_after_openai_enable.json
?? REHYDRATION_PACK/RUNS/B72/A/PROOF/order_status_preflight_prod.json
?? REHYDRATION_PACK/RUNS/B72/A/PROOF/order_status_preflight_prod.md
?? REHYDRATION_PACK/RUNS/B75/C/CHANGES.md
?? WorkerLambdaServiceRoleDefaultPolicyFC3707DA.json
?? checkruns.json
?? claude_gate_audit.json
?? temp_validate_log.txt
?? temp_validate_log2.txt
?? temp_validate_log3.txt
```

### python scripts/run_ci_checks.py --ci (third run after AWS SSO login)
```
[FAIL] Generated files changed after regen. Commit the regenerated outputs.
Uncommitted changes:
M backend/src/richpanel_middleware/commerce/order_lookup.py
M docs/00_Project_Admin/Progress_Log.md
M docs/_generated/doc_outline.json
M docs/_generated/doc_registry.compact.json
M docs/_generated/doc_registry.json
M docs/_generated/heading_index.json
M scripts/fixtures/order_lookup/shopify_order.json
M scripts/test_order_lookup.py
?? scripts/fixtures/order_lookup/shopify_order_gid.json
?? REHYDRATION_PACK/RUNS/RUN_20260211_2118Z/
?? .tmp.lambda_env.json
?? .tmp_pr_body_b76.md
?? .tmp_pr_body_b76_autogen.md
?? .tmp_required_checks.json
?? .tmp_required_checks_bugbot.json
?? .tmp_required_checks_restore.json
?? .tmp_required_checks_restore_again.json
?? REHYDRATION_PACK/RUNS/B75/B/PROOF/prod_ticket_116680_check.json
?? REHYDRATION_PACK/RUNS/B75/B/PROOF/prod_ticket_116680_check_after_botid_enable.json
?? REHYDRATION_PACK/RUNS/B75/B/PROOF/prod_ticket_116680_check_after_openai_enable.json
?? WorkerLambdaServiceRoleDefaultPolicyFC3707DA.json
?? checkruns.json
?? claude_gate_audit.json
?? temp_validate_log.txt
?? temp_validate_log2.txt
?? temp_validate_log3.txt
```

### python scripts/run_ci_checks.py --ci (after cleanup of unrelated files)
```
[FAIL] Generated files changed after regen. Commit the regenerated outputs.
Uncommitted changes:
M backend/src/richpanel_middleware/commerce/order_lookup.py
M docs/00_Project_Admin/Progress_Log.md
M docs/_generated/doc_outline.json
M docs/_generated/doc_registry.compact.json
M docs/_generated/doc_registry.json
M docs/_generated/heading_index.json
M scripts/fixtures/order_lookup/shopify_order.json
M scripts/test_order_lookup.py
?? scripts/fixtures/order_lookup/shopify_order_gid.json
?? REHYDRATION_PACK/RUNS/RUN_20260211_2118Z/
```

### python scripts/run_ci_checks.py --ci (clean tree)
```
[OK] CI-equivalent checks passed.
```
