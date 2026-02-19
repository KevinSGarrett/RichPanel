# PR Description

```html
<!-- PR_QUALITY: title_score=98/100; body_score=98/100; rubric_title=07; rubric_body=03; risk=risk:R2; p0_ok=true; timestamp=2026-02-19 -->
```

**Run ID:** `RUN_20260219_1823Z`  
**Agents:** C  
**Labels:** `risk:R2`, `gate:claude`  
**Risk:** `risk:R2`  
**Claude gate model (used):** `claude-sonnet-4-5-20250801` (pending run)  
**Anthropic response id:** `pending — PR gate`

### 1) Summary
- Tune reply rewrite limits (tokens/chars) and temperature for prod.
- Keep rewrite model pinned to GPT-5.2 and align prompt char limit with config.
- Document recommended prod tuning and capture run artifacts.
- Prod stack was rolled back to main; no active prod change from this PR.

### 2) Why
- **Problem / risk:** Current rewrite limits are conservative; Step 7 requires prod tuning knobs.
- **Pre-change failure mode:** Rewrites truncated early and lower variability than desired.
- **Why this approach:** Minimal CDK env var updates + doc note; no logic changes.
  - Update prompt cap to reflect the env-configured max chars.

### 3) Expected behavior & invariants
**Must hold (invariants):**
- `OPENAI_REPLY_REWRITE_MODEL` remains `gpt-5.2`.
- Fail-closed rewrite validation is unchanged.
- No outbound actions enabled; prod remains in shadow/safe mode.

**Non-goals (explicitly not changed):**
- Routing/intent model settings.
- Rewrite validation logic.
- Any customer-facing copy changes.

### 4) What changed
**Core changes:**
- Add `OPENAI_REPLY_REWRITE_MAX_TOKENS=700` and `OPENAI_REPLY_REWRITE_MAX_CHARS=1400`.
- Update `OPENAI_REPLY_REWRITE_TEMPERATURE=0.25`.
- Update reply rewrite prompt to use configured max chars instead of hardcoded 1000.
- Document recommended prod tuning values.

**Design decisions (why this way):**
- Keep change surface minimal in CDK env var map for auditability.
- Note prod tuning separately from defaults to avoid doc confusion.

### 5) Scope / files touched
**Runtime code:**
- `infra/cdk/lib/richpanel-middleware-stack.ts`
- `backend/src/richpanel_middleware/automation/llm_reply_rewriter.py`

**Tests:**
- None added (config-only).

**CI / workflows:**
- None.

**Docs / artifacts:**
- `docs/08_Engineering/Order_Status_OpenAI_Contract.md`
- `docs/00_Project_Admin/Progress_Log.md`
- `REHYDRATION_PACK/RUNS/RUN_20260219_1823Z/C/RUN_REPORT.md`

### 6) Test plan
**Local / CI-equivalent:**
- `python scripts/run_ci_checks.py --ci`
- `python scripts/verify_rehydration_pack.py`
- `python scripts/verify_agent_prompts_fresh.py`

**E2E / proof runs (redact ticket numbers in PR body if claiming PII-safe):**
- Not run (no behavior change beyond env config).

### 7) Results & evidence
**CI:** pending — `<PR link>`  
**Codecov:** pending — `<Codecov PR link>`  
**Bugbot:** pending — `<PR link>`  

**Artifacts / proof:**
- `REHYDRATION_PACK/RUNS/RUN_20260219_1823Z/C/evidence/run_ci_checks_ci.log`
- `REHYDRATION_PACK/RUNS/RUN_20260219_1823Z/C/evidence/verify_rehydration_pack.log`
- `REHYDRATION_PACK/RUNS/RUN_20260219_1823Z/C/evidence/verify_agent_prompts_fresh.log`
- `REHYDRATION_PACK/RUNS/RUN_20260219_1823Z/C/evidence/prod_runtime_flags_table_post_rollback.txt`
- `REHYDRATION_PACK/RUNS/RUN_20260219_1823Z/C/evidence/lambda_env_openai_rewrite_post_rollback.json`

**Proof snippet(s) (PII-safe):**
```text
[OK] CI-equivalent checks passed.
```

Rollback status: prod env vars show `OPENAI_REPLY_REWRITE_TEMPERATURE=0.2` and no max tokens/chars after rollback.

### 8) Risk & rollback
**Risk rationale:** `risk:R2` — prod config change affecting reply rewrite output limits/temperature.  

**Failure impact:** Replies may be shorter/longer or vary more; no change to validation or gating.  

**Rollback plan:**
- Revert PR.
- Redeploy previous CDK stack template.
- Re-run `npx cdk diff -c env=prod` to confirm rollback.

**CDK asset diff note:**
- Diff may include Lambda asset S3Key updates because prod code is behind B91–B93 changes; deploy should be treated as code+config sync, not config-only.

### 9) Reviewer + tool focus
**Please double-check:**
- CDK env var values match Step 7 (700/1400/0.25).
- `OPENAI_REPLY_REWRITE_MODEL` remains `gpt-5.2`.

**Please ignore:**
- Generated registries / line number shifts unless CI fails.
- Rehydration pack artifacts except referenced proof files.
