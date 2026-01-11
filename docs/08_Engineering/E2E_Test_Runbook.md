# E2E Test Runbook (for Cursor Agents)

Last updated: 2026-01-11
Status: Canonical

This runbook defines how to run and document end-to-end (E2E) smoke tests for the Richpanel middleware stack. These tests validate the full path from webhook ingress through worker processing to DynamoDB records.

---

## 1) When E2E tests are required
Run E2E smoke tests when a PR touches any automation or outbound paths:
- ackend/src/richpanel_middleware/automation/
- ackend/src/richpanel_middleware/integrations/
- ackend/src/lambda_handlers/
- infra/cdk/ (ingress/queue/worker resources)

Rule of thumb: if webhook → queue → worker → DynamoDB could be affected, run E2E.

---

## 2) Environments and workflows
| Workflow | Environment | When to run | Approval required |
|----------|-------------|-------------|-------------------|
| dev-e2e-smoke.yml | dev | After any automation/outbound change | No |
| staging-e2e-smoke.yml | staging | After staging deploy, before prod promotion | No |
| prod-e2e-smoke.yml | prod | After prod deploy only | Yes (PM/lead) |

---

## 3) What the smoke tests validate
- Ingress Lambda receives webhook
- Event enqueued to SQS
- Worker Lambda processes event
- DynamoDB records written:
  - Idempotency
  - Conversation state
  - Audit
- Routing/tagging confirmed (safe fields only)
- Order status draft reply presence/count (no message bodies)
- CloudWatch dashboard/alarm names surfaced when available

**No PII in artifacts.** Record only safe identifiers, URLs, derived table names, and counts.

---

## 4) Dev E2E smoke (PowerShell-safe)
`powershell
 = "evt:" + (Get-Date -Format 'yyyyMMddHHmmss')
gh workflow run dev-e2e-smoke.yml --ref (git branch --show-current) -f event-id=
gh run watch --exit-status
gh run view --json url --jq '.url'
`
Evidence to capture in TEST_MATRIX.md:
- Run URL
- Pass/fail
- DynamoDB confirmations (event_id + conversation_id observed)
- Console links (DynamoDB tables, CloudWatch logs)
- CloudWatch dashboard/alarm names (or note none surfaced)
- Routing + draft reply confirmations (safe fields only)

---

## 5) Staging E2E smoke
`powershell
 = "evt:" + (Get-Date -Format 'yyyyMMddHHmmss')
gh workflow run staging-e2e-smoke.yml --ref main -f event-id=
 = gh run list --workflow staging-e2e-smoke.yml --branch main --limit 1 --json databaseId --jq '.[0].databaseId'
gh run watch  --exit-status
 = gh run view  --json url --jq '.url'

`
Capture the same evidence as dev. If staging fails, stop promotion to prod and open an issue.

---

## 6) Prod E2E smoke (with explicit approval)
`powershell
 = "evt:" + (Get-Date -Format 'yyyyMMddHHmmss')
gh workflow run prod-e2e-smoke.yml --ref main -f event-id=
 = gh run list --workflow prod-e2e-smoke.yml --branch main --limit 1 --json databaseId --jq '.[0].databaseId'
gh run watch  --exit-status
 = gh run view  --json url --jq '.url'

`
Only run after PM/lead go/no-go. Record run URL, approval name/time, and evidence in TEST_MATRIX.md.

---

## 7) Evidence capture (all environments)
Record in REHYDRATION_PACK/RUNS/<RUN_ID>/<AGENT_ID>/TEST_MATRIX.md:
- Workflow run URL and status
- DynamoDB confirmations (event_id + conversation_id observed)
- DynamoDB console links for idempotency/conversation_state/audit tables
- CloudWatch dashboard and alarm names (or “none surfaced”)
- Routing + draft reply confirmations (safe fields only)
- Note any fallbacks or missing outputs

Add a summary line in RUN_REPORT.md under PR Health Check.

---

## 8) Failure triage
1) Capture the failing run URL and log excerpt in RUN_REPORT.md.
2) Classify failure:
   - Ingress/queue/worker/DynamoDB/validation
3) Reproduce locally if possible:
   - python scripts/dev_e2e_smoke.py (requires AWS creds)
4) Fix or escalate:
   - If quick fix, rerun workflow
   - If unclear, record in REHYDRATION_PACK/OPEN_QUESTIONS.md and notify PM
5) Document remediation plan and results in run artifacts.

---

## 9) Template snippet for TEST_MATRIX.md
`markdown
## E2E Smoke Tests

### Dev E2E Smoke
- Run URL: <URL>
- Status: pass/fail
- DynamoDB: idempotency/conversation_state/audit observed (event_id + conversation_id)
- Console links: <DDB links>
- CloudWatch: dashboard=<name|none>, alarms=<list|none>
- Routing: <summary>
- Draft reply: <present/absent + count>

### Staging E2E Smoke
- Run URL: <URL or "not run">
- Status: pass/fail/N/A

### Prod E2E Smoke
- Run URL: <URL or "not run">
- Status: pass/fail/N/A
- Approval: <name + timestamp>
`

---

## 10) Checklist
- [ ] Determined if E2E required for this PR
- [ ] Ran required E2E workflow(s)
- [ ] Captured run URLs and confirmations in TEST_MATRIX.md
- [ ] No PII in artifacts (IDs/URLs only)
- [ ] Added PR Health Check summary in RUN_REPORT.md
