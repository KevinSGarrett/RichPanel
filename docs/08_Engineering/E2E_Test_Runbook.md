# E2E Test Runbook (for Cursor Agents)

Last updated: 2026-01-11  
Status: Canonical

This runbook defines end-to-end (E2E) testing procedures for the RichPanel middleware stack. E2E smoke tests validate that the entire event flow — from webhook ingress through worker processing to DynamoDB persistence — works correctly in deployed environments.

---

## 1) When E2E tests are required

E2E smoke tests are **mandatory** when any PR touches:
- `backend/src/richpanel_middleware/automation/` (routing, pipeline, LLM logic)
- `backend/src/richpanel_middleware/integrations/` (Richpanel, OpenAI, Shopify, ShipStation clients)
- `backend/src/lambda_handlers/` (ingress, worker handlers)
- `infra/cdk/` (if ingress URL, queue, worker, or DynamoDB resources change)

**Rule of thumb:** If your change affects how events flow from Richpanel webhooks to DynamoDB records, run E2E tests.

---

## 2) E2E smoke test environments

We have three E2E smoke workflows, one for each environment:

| Workflow | Environment | When to run | Approval required |
|----------|-------------|-------------|-------------------|
| `dev-e2e-smoke.yml` | dev (151124909266) | After any automation/outbound change | No |
| `staging-e2e-smoke.yml` | staging (260475105304) | After staging deploy, before prod promotion | No |
| `prod-e2e-smoke.yml` | prod (TBD) | After prod deploy only | Yes (PM/lead) |

---

## 3) What E2E smoke tests validate

Each E2E smoke test:
1. Sends a synthetic webhook to the ingress Lambda
2. Confirms the event is queued to SQS
3. Confirms the worker Lambda processes the event
4. Validates DynamoDB records are written:
   - **Idempotency table**: event deduplication record
   - **Conversation state table**: conversation context and history
   - **Audit table**: audit trail record
5. Checks routing/tagging logic (safe fields only, no PII)
6. Validates order status draft reply generation (counts, not content)
7. Surfaces CloudWatch dashboard and alarm names (if configured)

**What is NOT tested:**
- Real Richpanel API calls (mocked/offline where possible)
- Real OpenAI API calls (uses test prompts)
- Real Shopify/ShipStation API calls (fixtures or dry-run)
- Production data (uses synthetic event IDs)

---

## 4) Dev E2E smoke test

### When to run
- After touching any automation/outbound logic
- Before pushing your PR
- After merging to main (as a sanity check)

### How to run (PowerShell-safe)
```powershell
# Generate a unique event ID
$eventId = "evt:" + (Get-Date -Format 'yyyyMMddHHmmss')

# Trigger the workflow (replace <branch-name> with your branch)
gh workflow run dev-e2e-smoke.yml --ref <branch-name> -f event-id=$eventId

# Watch the workflow in real-time
gh run watch --exit-status

# Get the run URL for evidence capture
gh run view --json url --jq '.url'
```

### Expected outputs
The workflow writes a job summary to `${GITHUB_STEP_SUMMARY}` with:
- Ingress Lambda URL (safe to capture)
- SQS queue URL (safe to capture)
- DynamoDB table names (safe to capture)
- Log group names (safe to capture)
- CloudWatch Logs console deep links (safe to capture)
- Confirmation that idempotency, conversation state, and audit records were written
- Event ID and conversation ID observed in records
- Routing category and tags (safe fields only)
- Order status draft reply presence and draft count

### Evidence capture
Copy to `REHYDRATION_PACK/RUNS/<RUN_ID>/<AGENT_ID>/TEST_MATRIX.md`:
- GitHub Actions run URL
- Pass/fail status
- DynamoDB confirmations (event_id + conversation_id observed)
- DynamoDB console links for each table
- CloudWatch dashboard name and alarm names (or "no dashboards/alarms surfaced")
- Routing + draft confirmation lines (safe fields only)

### Troubleshooting
**Workflow fails with "CloudFormation outputs not found":**
- The script falls back to derived values (stack name + resource naming conventions)
- Capture the warning lines from the output
- This is advisory only; does not block the test

**Worker Lambda times out:**
- Check CloudWatch Logs for the worker Lambda
- Look for API rate limits, network errors, or timeout issues
- If using real tokens, verify they're not expired

**DynamoDB records not found:**
- Verify the event_id was unique (not reused from a previous run)
- Check worker Lambda logs for errors
- Confirm idempotency table exists and has correct permissions

---

## 5) Staging E2E smoke test

### When to run
- **Always** after deploying to staging (via `Deploy Staging Stack` workflow)
- Before promoting changes to prod
- As part of staging validation during PR health check

### How to run (PowerShell-safe)
```powershell
# Generate a unique event ID
$eventId = "evt:" + (Get-Date -Format 'yyyyMMddHHmmss')

# Trigger the workflow (always use --ref main for staging)
gh workflow run staging-e2e-smoke.yml --ref main -f event-id=$eventId

# Get the run ID and watch it
$runId = gh run list --workflow staging-e2e-smoke.yml --branch main --limit 1 --json databaseId --jq '.[0].databaseId'
gh run watch $runId --exit-status

# Get the run URL
$runUrl = gh run view $runId --json url --jq '.url'
$runUrl
```

### Expected outputs
Same as dev E2E smoke test, but against staging environment resources.

### Evidence capture
Same as dev E2E smoke test. Record in `REHYDRATION_PACK/RUNS/<RUN_ID>/<AGENT_ID>/TEST_MATRIX.md`.

### Staging-specific notes
- Run against `--ref main` to prove the deployed artifact is healthy
- `gh run list` scoped to `staging-e2e-smoke.yml` + `--branch main` surfaces the run you just dispatched
- If the test fails, **stop prod promotion** and open a defect

---

## 6) Prod E2E smoke test

### When to run
- **Only after deploying to prod** (via `Deploy Prod Stack` workflow)
- Requires explicit PM/lead approval (go/no-go recorded in rehydration pack)

### How to run (PowerShell-safe)
```powershell
# Generate a unique event ID
$eventId = "evt:" + (Get-Date -Format 'yyyyMMddHHmmss')

# Trigger the workflow (always use --ref main for prod)
gh workflow run prod-e2e-smoke.yml --ref main -f event-id=$eventId

# Get the run ID and watch it
$runId = gh run list --workflow prod-e2e-smoke.yml --branch main --limit 1 --json databaseId --jq '.[0].databaseId'
gh run watch $runId --exit-status

# Get the run URL
$runUrl = gh run view $runId --json url --jq '.url'
$runUrl
```

### Expected outputs
Same as dev and staging E2E smoke tests, but against prod environment resources.

### Evidence capture
Record in `REHYDRATION_PACK/RUNS/<RUN_ID>/<AGENT_ID>/TEST_MATRIX.md`:
- Prod E2E run URL
- Pass/fail status
- Go/no-go approval (name + timestamp)
- DynamoDB confirmations and console links
- CloudWatch dashboard and alarm names

### Prod-specific notes
- **Never run without PM/lead approval**
- **Never run during production business hours** (unless emergency validation)
- If the test fails, escalate immediately and document in `REHYDRATION_PACK/OPEN_QUESTIONS.md`

---

## 7) E2E test evidence requirements

Every E2E test run must capture:
1. **GitHub Actions run URL** (full URL, not just run ID)
2. **Pass/fail status** (from `gh run watch --exit-status`)
3. **Job summary contents** (copy from GitHub Actions Summary tab):
   - Ingress URL
   - Queue URL
   - DynamoDB table names + console links
   - Log group names + CloudWatch Logs links
   - CloudWatch dashboard name (if surfaced)
   - CloudWatch alarm names (if surfaced)
4. **DynamoDB confirmations**:
   - Idempotency record observed (event_id)
   - Conversation state record observed (conversation_id)
   - Audit record observed (event_id + conversation_id)
5. **Routing + draft confirmations** (safe fields only):
   - Routing category/tags
   - Order status draft reply presence
   - Draft replies count

**No PII, no secrets, no message bodies** — only safe identifiers and counts.

---

## 8) E2E test failure triage

If an E2E smoke test fails, follow this triage process:

### Step 1 — Capture the failure
- Copy the GitHub Actions run URL
- Copy the job log excerpt showing the failure
- Record in `REHYDRATION_PACK/RUNS/<RUN_ID>/<AGENT_ID>/RUN_REPORT.md`

### Step 2 — Classify the failure
- **Ingress failure**: webhook not accepted (check ingress Lambda logs, auth tokens)
- **Queue failure**: event not queued (check SQS permissions, queue URL)
- **Worker failure**: Lambda timeout or error (check worker Lambda logs, API rate limits)
- **DynamoDB failure**: records not written (check table permissions, capacity)
- **Validation failure**: records written but fields incorrect (check worker logic)

### Step 3 — Reproduce locally (if possible)
- Run `python scripts/dev_e2e_smoke.py` locally (requires AWS credentials)
- Or run unit tests: `python scripts/test_pipeline_handlers.py`

### Step 4 — Fix or escalate
- If you can fix quickly (e.g., typo, missing env var), fix and rerun
- If root cause is unclear, escalate to PM via `REHYDRATION_PACK/OPEN_QUESTIONS.md`
- If blocking prod promotion, open an issue and notify PM immediately

### Step 5 — Document the fix
- Add/update `docs/00_Project_Admin/Issue_Log.md`
- Create an issue detail file: `docs/00_Project_Admin/Issues/<ISSUE_ID>.md`
- Include root cause analysis and prevention notes

---

## 9) E2E test evidence templates

### TEST_MATRIX.md template (E2E section)

```markdown
## E2E Smoke Tests

### Dev E2E Smoke
- **Run URL**: <GITHUB_ACTIONS_RUN_URL>
- **Status**: pass/fail
- **Event ID**: evt:<YYYYMMDDHHMMSS>
- **DynamoDB confirmations**:
  - Idempotency table: rp-mw-dev-idempotency (event_id observed)
  - Conversation state table: rp-mw-dev-conversation-state (conversation_id observed)
  - Audit table: rp-mw-dev-audit (event_id + conversation_id observed)
- **Console links**:
  - [Idempotency table](<DYNAMODB_CONSOLE_URL>)
  - [Conversation state table](<DYNAMODB_CONSOLE_URL>)
  - [Audit table](<DYNAMODB_CONSOLE_URL>)
- **CloudWatch**:
  - Dashboard: rp-mw-dev-ops (or "no dashboards surfaced")
  - Alarms: rp-mw-dev-dlq-depth, rp-mw-dev-worker-errors, rp-mw-dev-worker-throttles, rp-mw-dev-ingress-errors (or "no alarms surfaced")
- **Routing**: category=order_status, tags=["order_inquiry"] (safe fields only)
- **Draft reply**: order_status_draft_reply present, draft_replies count=1

### Staging E2E Smoke
- **Run URL**: <GITHUB_ACTIONS_RUN_URL or "not run yet">
- **Status**: pass/fail/N/A
- (Same fields as dev)

### Prod E2E Smoke
- **Run URL**: <GITHUB_ACTIONS_RUN_URL or "awaiting PM approval">
- **Status**: pass/fail/N/A
- **Go/no-go approval**: <NAME + TIMESTAMP or "not approved yet">
- (Same fields as dev)
```

### RUN_REPORT.md template (PR Health Check E2E section)

```markdown
### E2E Testing (if automation/outbound touched)
- **E2E tests required**: yes/no
- **Dev E2E run URL**: <GITHUB_ACTIONS_RUN_URL or N/A>
- **Staging E2E run URL**: <GITHUB_ACTIONS_RUN_URL or N/A>
- **Prod E2E run URL**: <GITHUB_ACTIONS_RUN_URL or N/A>
- **E2E results**: all pass / failures documented / N/A
- **Evidence location**: `REHYDRATION_PACK/RUNS/<RUN_ID>/<AGENT_ID>/TEST_MATRIX.md`
```

---

## 10) Common E2E test pitfalls

### Reusing event IDs
- **Problem**: DynamoDB idempotency deduplication prevents duplicate event processing
- **Solution**: Always generate a new event ID with timestamp: `evt:$(Get-Date -Format 'yyyyMMddHHmmss')`

### Missing Secrets Manager entries
- **Problem**: Worker Lambda can't call APIs without credentials
- **Solution**: Run `seed-secrets.yml` workflow to upsert missing secrets (dev/staging only)

### Expired API tokens
- **Problem**: OpenAI/Shopify/ShipStation calls fail with 401/403
- **Solution**: Rotate tokens in Secrets Manager (see `docs/06_Security_Secrets/Secrets_Management_Policy.md`)

### CloudFormation outputs not found
- **Problem**: Script can't auto-discover resource URLs/ARNs
- **Solution**: This is advisory only; script falls back to derived values. Capture the warning but don't block.

### False positives on routing/drafts
- **Problem**: Test expects specific routing category but gets different one
- **Solution**: Check if routing logic changed intentionally. If so, update test expectations in `scripts/dev_e2e_smoke.py`.

---

## 11) Local E2E testing (advanced)

For rapid iteration, you can run E2E smoke tests locally (requires AWS credentials):

```powershell
# Set AWS region
$env:AWS_REGION = "us-east-2"
$env:AWS_DEFAULT_REGION = $env:AWS_REGION

# Run dev E2E smoke locally
python scripts/dev_e2e_smoke.py

# Or run with explicit event ID
python scripts/dev_e2e_smoke.py --event-id evt:20260111163800
```

**Requirements:**
- AWS credentials configured (IAM user or OIDC role)
- Permissions to invoke Lambda, read SQS, query DynamoDB, read CloudWatch Logs
- Network access to AWS us-east-2 region

**Limitations:**
- Local runs don't produce GitHub Actions job summaries
- Must manually capture output for evidence
- Not suitable for staging/prod (use workflows instead)

---

## 12) Summary checklist

Before marking E2E testing complete:
- [ ] Identified if PR touches automation/outbound paths
- [ ] Ran dev E2E smoke test (if required)
- [ ] Captured dev E2E run URL + pass/fail in TEST_MATRIX.md
- [ ] Ran staging E2E smoke test after staging deploy (if required)
- [ ] Captured staging E2E run URL + pass/fail in TEST_MATRIX.md
- [ ] Prod E2E smoke deferred until post-deploy with PM approval
- [ ] All evidence includes DynamoDB confirmations (no placeholders)
- [ ] CloudWatch dashboard/alarm names surfaced (or "no dashboards/alarms surfaced")
- [ ] Routing + draft confirmations captured (safe fields only, no PII)
- [ ] Any failures documented with triage notes and remediation plan
