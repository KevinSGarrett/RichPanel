<!-- PR_QUALITY: title_score=96/100; body_score=97/100; rubric_title=07; rubric_body=03; risk=risk:R2; p0_ok=true; timestamp=2026-01-28 -->

**Run ID:** `RUN_20260128_1719Z`  
**Agents:** C  
**Labels:** `risk:R2`, `gate:claude`  
**Risk:** `risk:R2`  
**Claude gate model (used):** `claude-opus-4-5-20251101`  
**Anthropic response id:** `msg_01HdCvJbez2AXRFX4Vgps1Vr`  
**Anthropic request id:** `req_011CXaAjeqHX3cNJzRjvXkU3`  
**Anthropic usage:** input_tokens=26252; output_tokens=600; cache_creation_input_tokens=0; cache_read_input_tokens=0; service_tier=standard

### 1) Summary
- Produced a repeatable live read-only shadow report with stable filenames and required deployment-gate metrics.
- Enforced outbound-disabled guardrails and added `--max-tickets`/`--out`/env selection for reproducible runs.
- Updated the nightly workflow and prod runbook with gate criteria and new report outputs.
- Added ticket-fetch failure handling so stale ticket IDs no longer abort the report run.
- Added `shopify-token-source` input to select the correct prod Shopify token.

### 2) Why
- **Problem / risk:** The live shadow validation was a one-off script run with non-deterministic outputs and no gate-ready summary.
- **Pre-change failure mode:** CI could not reliably collect artifacts or enforce outbound-off guarantees for prod read-only runs.
- **Why this approach:** Add stable report outputs + explicit guardrails so the run can be scheduled and used as a deploy gate.

### 3) Expected behavior & invariants
**Must hold (invariants):**
- `RICHPANEL_OUTBOUND_ENABLED=false` and `RICHPANEL_WRITE_DISABLED=true` are required for live shadow eval.
- Richpanel/Shopify/ShipStation requests remain GET/HEAD only; any write attempt fails closed.
- JSON/MD reports remain PII-safe (no raw ticket IDs, emails, or message bodies).
- Report JSON includes `ticket_count`, `match_success_rate`, `match_failure_buckets`, `tracking_or_eta_available_rate`, and `would_reply_send`.

**Non-goals (explicitly not changed):**
- Production routing logic, outbound reply logic, or write paths outside the shadow eval script.
- Shopify/Richpanel client behavior beyond read-only guards already in place.

### 4) What changed
**Core changes:**
- Added CLI support for `--max-tickets`, `--env`, `--region`, `--stack-name`, `--out`, and `--summary-md-out`.
- Added match-failure buckets, tracking/ETA availability rate, and `would_reply_send` to the report schema.
- Enforced outbound-disabled guard in `scripts/live_readonly_shadow_eval.py`.
- Updated the nightly workflow to emit `live_shadow_report.json` and `live_shadow_summary.md`.
- Added `--allow-ticket-fetch-failures` and a `ticket-ids=__none__` override for stale secrets.
- Added `shopify-token-source` input to force the API token when admin tokens are stale.

**Design decisions (why this way):**
- Use `--out` to produce stable artifact filenames for CI uploads and deployment-gate automation.
- Keep gate decisions in the report rather than hard-failing so reviewers can review drift first.

### 5) Scope / files touched
**Runtime code:**
- `scripts/live_readonly_shadow_eval.py`
- `scripts/readonly_shadow_utils.py`

**Tests:**
- `scripts/test_live_readonly_shadow_eval.py`

**CI / workflows:**
- `.github/workflows/shadow_live_readonly_eval.yml`

**Docs / artifacts:**
- `docs/08_Engineering/Prod_ReadOnly_Shadow_Mode_Runbook.md`
- `REHYDRATION_PACK/RUNS/B62/C/RUN_REPORT.md`
- `REHYDRATION_PACK/RUNS/B62/C/CHANGES.md`
- `REHYDRATION_PACK/RUNS/B62/C/EVIDENCE.md`
- `REHYDRATION_PACK/RUNS/B62/C/PROOF/live_shadow_report.json`
- `REHYDRATION_PACK/RUNS/B62/C/PROOF/live_shadow_summary.md`

**Hot files:**
- `scripts/live_readonly_shadow_eval.py`
- `.github/workflows/shadow_live_readonly_eval.yml`
- `docs/08_Engineering/Prod_ReadOnly_Shadow_Mode_Runbook.md`

### 6) Test plan
**Local / CI-equivalent:**
- `python scripts/test_live_readonly_shadow_eval.py`

**E2E / proof runs (redact ticket numbers in PR body if claiming PII-safe):**
- `python REHYDRATION_PACK/RUNS/B62/C/PROOF/generate_sample_report.py`

### 7) Results & evidence
**CI:** https://github.com/KevinSGarrett/RichPanel/actions/runs/21448589779  
**Codecov:** pending - https://codecov.io/gh/KevinSGarrett/RichPanel  
**Bugbot:** pending - https://github.com/KevinSGarrett/RichPanel (trigger via `@cursor review`)  
**Claude gate:** https://github.com/KevinSGarrett/RichPanel/actions/runs/21448599396

**Artifacts / proof:**
- `REHYDRATION_PACK/RUNS/B62/C/PROOF/live_shadow_report.json`
- `REHYDRATION_PACK/RUNS/B62/C/PROOF/live_shadow_summary.json`
- `REHYDRATION_PACK/RUNS/B62/C/PROOF/live_shadow_summary.md`
- `REHYDRATION_PACK/RUNS/B62/C/PROOF/live_shadow_http_trace.json`

**Proof snippet(s) (PII-safe):**
```text
ticket_count: 17
match_success_rate: 1.0
tracking_or_eta_available_rate: 1.0
would_reply_send: false
drift_watch.has_alerts: true
shopify_probe.status_code: 200
http_trace_summary.allowed_methods_only: true
```

### 8) Risk & rollback
**Risk rationale:** `risk:R2` — changes touch prod-read-only guardrails and CI scheduling, but do not alter write paths.

**Failure impact:** deploy gate metrics or nightly workflow could misreport or fail to upload artifacts.

**Rollback plan:**
- Revert this PR.
- Re-run `shadow_live_readonly_eval.yml` to verify legacy report outputs still work.

### 9) Reviewer + tool focus
**Please double-check:**
- `scripts/live_readonly_shadow_eval.py` guardrails and output schema.
- `shadow_live_readonly_eval.yml` env flags and `--out` usage.
- Runbook gate criteria wording (no false positives).

**Please ignore:**
- Rehydration pack artifacts other than B62/C proof files.
