# Test Matrix

**RUN_ID:** RUN_20260113_0433Z  
**Agent:** B  
**Date:** 2026-01-13

## Tests Run

| Test Name | Command | Pass/Fail | Evidence |
|---|---|---|---|
| CI-equivalent checks | `python scripts/run_ci_checks.py` | ✅ PASS | Local output: 108 tests OK; doc hygiene, admin logs sync, OpenAI model defaults all passed |
| URL encoding unit tests | `python scripts/test_e2e_smoke_encoding.py` | ✅ PASS | 5 tests OK (email ID encoding, + sign encoding, scenario determinism, PII-safety) |
| Order-status E2E proof (DEV) | `python scripts/dev_e2e_smoke.py --env dev ... --scenario order_status` | ✅ PASS | `REHYDRATION_PACK/RUNS/RUN_20260113_0433Z/B/e2e_outbound_proof.json` |

## Test Details

### CI-Equivalent Checks
**Command:**
```
python scripts/run_ci_checks.py
```

**Output Summary:**
- Doc registries regenerated (402 docs, 365 reference files)
- Plan checklist extracted (601 items)
- REHYDRATION_PACK validated (build mode)
- Doc hygiene: no banned placeholders
- Secret inventory in sync
- Admin logs sync: RUN_20260113_0433Z referenced
- GPT-5.x defaults enforced
- 108 unit tests passed across all modules
- No protected deletes detected

**Exit Code:** 0

### URL Encoding Unit Tests
**File:** `scripts/test_e2e_smoke_encoding.py`

**Tests:**
1. `test_order_status_scenario_includes_required_fields` - Validates scenario payload has tracking_number, carrier, shipping_method, etc.
2. `test_order_status_scenario_is_deterministic` - Ensures same run_id produces same tracking numbers
3. `test_order_status_scenario_no_pii` - Confirms no @, %40, mail. patterns
4. `test_middleware_encodes_email_based_conversation_id` - Asserts special chars (@, <, >) are percent-encoded in API paths
5. `test_middleware_encodes_plus_sign_in_conversation_id` - Asserts + becomes %2B in paths

**Result:** 5/5 passed in 0.011s

### Order-Status E2E Proof (DEV)
**Ticket:** 1035 (id fingerprint: b3e3ba4d2e9c)  
**Event ID:** `evt:ab220b09-d267-45d8-b6ea-a879da2d0c4f`

**Proof Evidence:**
- Webhook accepted by ingress: ✓
- DynamoDB records written:
  - Idempotency: `rp_mw_dev_idempotency` (status=processed, mode=automation_candidate)
  - Conversation state: `rp_mw_dev_conversation_state` (routing.intent=order_status_tracking, action_count=2)
  - Audit trail: `rp_mw_dev_audit_trail` (routing.category=order_status)
- Routing intent matched: `order_status_tracking` ✓
- Draft replies persisted (redacted format with prompt_fingerprint) ✓
- Middleware tags applied:
  - `mw-skip-status-read-failed` (escalation path)
  - `route-email-support-team` (routing applied)
- Test tag verified: `mw-smoke:RUN_20260113_0433Z` ✓
- PII guard: PASS (no raw ticket IDs, paths redacted) ✓

**DynamoDB Console Links:**
- Idempotency: https://us-east-2.console.aws.amazon.com/dynamodbv2/home?region=us-east-2#item-explorer?initialTagKey=&initialTagValue=&table=rp_mw_dev_idempotency
- Conversation state: https://us-east-2.console.aws.amazon.com/dynamodbv2/home?region=us-east-2#item-explorer?initialTagKey=&initialTagValue=&table=rp_mw_dev_conversation_state
- Audit trail: https://us-east-2.console.aws.amazon.com/dynamodbv2/home?region=us-east-2#item-explorer?initialTagKey=&initialTagValue=&table=rp_mw_dev_audit_trail

**CloudWatch Logs:**
- Log group: `/aws/lambda/rp-mw-dev-worker`
- Console: https://us-east-2.console.aws.amazon.com/cloudwatch/home?region=us-east-2#logsV2:log-groups/log-group/$252Faws$252Flambda$252Frp-mw-dev-worker

**Ticket State:**
- Pre: status=OPEN, tags included previous run smoke tags
- Post: status=OPEN, tags added `mw-skip-status-read-failed`, `route-email-support-team`
- updated_at delta: 122.155s

## Unit Test Assertion Examples

### URL Encoding Enforcement
From `test_middleware_encodes_email_based_conversation_id`:
```python
# Create envelope with email-based ID containing special chars
email_id = "<test@mail.example.com>"
envelope = EventEnvelope(conversation_id=email_id, ...)

# Execute routing tags with mocked executor
execute_routing_tags(envelope, plan, ..., richpanel_executor=mock_executor)

# Assert path is URL-encoded
path_arg = mock_executor.execute.call_args[0][1]
self.assertNotIn("<", path_arg)  # Raw chars removed
self.assertNotIn("@", path_arg)
self.assertIn("%", path_arg)      # Percent-encoded
```

### Scenario Payload Coverage
From `test_order_status_scenario_includes_required_fields`:
```python
payload = _order_status_scenario_payload("TEST_RUN", conversation_id="test-123")

self.assertEqual(payload["scenario"], "order_status")
self.assertEqual(payload["intent"], "order_status_tracking")
self.assertIn("customer_message", payload)
self.assertIn("tracking_number", payload)
self.assertIn("carrier", payload)
self.assertIn("shipping_method", payload)
```

## Coverage Notes
- URL encoding now enforced by unit tests (2 tests)
- Scenario payload validated for required fields (3 tests)
- Existing outbound tests still pass (confirms no regression)
- Total test count: 108 (up from 103)
