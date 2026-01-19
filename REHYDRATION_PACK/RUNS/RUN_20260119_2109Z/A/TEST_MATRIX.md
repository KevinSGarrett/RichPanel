# TEST MATRIX — RUN_20260119_2109Z — Agent A

## Local CI Checks
| Check | Status | Details |
|-------|--------|---------|
| Doc registry regeneration | ✅ PASS | 405 docs indexed |
| Reference registry | ✅ PASS | 365 files |
| Plan checklist extraction | ✅ PASS | 639 items extracted |
| Rehydration pack validation | ✅ PASS | Build mode validated |
| Doc hygiene | ✅ PASS | No ambiguous placeholders after fixes |
| Secret inventory sync | ✅ PASS | In sync with code defaults |
| Admin logs sync | ✅ PASS | RUN_20260119_0255Z referenced |
| Protected deletes check | ✅ PASS | No unapproved deletions |

## Unit Tests Executed
| Test Suite | Tests | Status | Notes |
|------------|-------|--------|-------|
| test_delivery_estimate.py | 6 | ✅ PASS | Business days, windows, normalization |
| test_pipeline_handlers.py | 43 | ✅ PASS | DDB sanitization, routing, outbound, flags |
| test_richpanel_client.py | 12 | ✅ PASS | Dry run, retries, redaction |
| test_openai_client.py | 9 | ✅ PASS | Safe mode, offline eval, secrets |
| test_shopify_client.py | 8 | ✅ PASS | Network gates, retries, token redaction |
| test_shipstation_client.py | 8 | ✅ PASS | Executor flags, retries, credentials |
| test_order_lookup.py | 14 | ✅ PASS | Payload extraction, enrichment |
| test_llm_reply_rewriter.py | 7 | ✅ PASS | Confidence gating, parse fallbacks |
| test_llm_routing.py | 15 | ✅ PASS | Gating, artifacts, primary flags |
| test_worker_handler_flag_wiring.py | 3 | ✅ PASS | Flag propagation |
| test_read_only_shadow_mode.py | 2 | ✅ PASS | Shadow reads without writes |
| test_e2e_smoke_encoding.py | 17 | ✅ PASS | URL encoding, PII guards, criteria |
| **test_claude_gate_review.py** | **30+** | ✅ **PASS** | **NEW: Gate script tests** |

## New Test File Details
**File**: `scripts/test_claude_gate_review.py`

### Coverage by Category
| Category | Test Cases | Notes |
|----------|-----------|-------|
| Risk label parsing | 4 | Valid, suffix, missing, multiple |
| Model selection | 5 | R0→Haiku, R1→Sonnet, R2/R3/R4→Opus |
| Verdict parsing | 3 | PASS, FAIL, missing defaults to FAIL |
| Findings extraction | 2 | Standard and max limit enforcement |
| Response text extraction | 2 | Multi-chunk and empty content |
| Comment formatting | 2 | With and without response ID/usage |
| Text utilities | 2 | Truncation behavior |
| Prompt building | 1 | All required sections present |
| False positive detection | 2 | All approved vs mixed |
| GitHub Actions integration | 1 | Output file writing |
| Environment handling | 2 | Present vs missing env vars |
| API mocking | 1 | Successful Anthropic request |
| Main function behavior | 2 | Skip without label, fail without key |

### Key Test Scenarios
1. **Risk label normalization with suffix** - Ensures `risk:R1-low` normalizes to `risk:R1`
2. **Opus selection for R2/R3/R4** - Validates new model mapping
3. **Response ID in comment** - Confirms audit trail is present
4. **Token usage in comment** - Confirms cost transparency
5. **Skip when gate:claude missing** - Validates old behavior (will be obsolete with auto-apply)
6. **Fail when ANTHROPIC_API_KEY missing** - Fail-closed security

## GitHub Actions Checks
| Check | Status | Details |
|-------|--------|---------|
| PR Created | ✅ DONE | PR #126 created |
| CI Workflow | 🔄 PENDING | Waiting for completion |
| Codecov | 🔄 PENDING | Waiting for upload and status |
| Bugbot | 🔄 PENDING | Triggered via comment |
| Claude Gate | 🔄 PENDING | Will auto-run with label |

## Evidence Collection Plan
- [ ] Capture final CI workflow URL
- [ ] Capture Codecov patch coverage percentage
- [ ] Capture Bugbot review comment with findings
- [ ] **Capture Claude gate PR comment with response ID and token usage**
- [ ] Screenshot or copy Claude gate comment showing `msg_...` and token counts
- [ ] Cross-reference response ID in Anthropic dashboard (if access available)

## Expected Outcomes
1. **Codecov**: Patch coverage ≥50% (new test file should be high coverage)
2. **Bugbot**: Clean review or approved patterns only
3. **Claude Gate**: 
   - PASS verdict (clean PR, well-tested)
   - Response ID present (e.g., `msg_abc123xyz`)
   - Token usage displayed (e.g., `input=2000, output=150`)
   - Model: `claude-opus-4-5-20251101` (because risk:R2)

## Test Execution Commands
```powershell
# Local CI checks
python scripts/run_ci_checks.py --ci

# Run new test file standalone
python scripts/test_claude_gate_review.py

# Run all tests
python -m unittest discover -s scripts -p "test_*.py"
```

## Status Summary
- **Local Tests**: ✅ All passing (148 tests total)
- **CI Checks**: ✅ Exit code 0
- **GitHub Actions**: 🔄 In progress
- **Ready for Merge**: ❌ Waiting for gates
