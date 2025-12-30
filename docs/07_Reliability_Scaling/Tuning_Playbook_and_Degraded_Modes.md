# Tuning Playbook and Degraded Modes (v1)

Last updated: 2025-12-22  
Status: **Final (Wave 07)**

This playbook tells operators **exactly what to change** when reliability issues occur (backlogs, 429s, vendor outages) without breaking safety guarantees.

**Key principle:** the system must always be able to fall back to **route-only** behavior.

Related:
- Kill switch / safe mode: `docs/06_Security_Privacy_Compliance/Kill_Switch_and_Safe_Mode.md`
- Parameter defaults: `docs/07_Reliability_Scaling/parameter_defaults_v1.yaml`
- Backlog replay: `docs/07_Reliability_Scaling/Backlog_Catchup_and_Replay_Strategy.md`

---

## 1) Observability signals to watch
These are the signals used in all playbooks below:

- **SQS oldest message age** (queue lag)
- **SQS approx. number of messages visible** (backlog)
- **Worker Lambda error rate** (5xx / uncaught)
- **Worker Lambda throttles** (reserved concurrency too low or account concurrency issues)
- **Vendor error/429 rates**
  - Richpanel 429 + Retry-After
  - OpenAI timeouts / 429 / 5xx
  - Shopify timeouts (if enabled)
- **Cost guardrails**
  - tokens/message p95
  - total requests/hour

---

## 2) Degraded modes

### A) Safe mode (Route-only)
**What it does:**
- Continues routing/tagging/assignment recommendations
- **Disables all customer-facing automated replies**

**How to enable:** set runtime flag `safe_mode=true` (SSM)

**When to use:**
- vendor instability (OpenAI/Richpanel) is causing retries or timeouts
- backlog grows faster than drain rate
- any sign of automation safety issues

### B) Disable automation
**What it does:**
- Similar to safe mode, but leaves room for certain non-message actions
- **Strongly recommended:** treat as “no auto messages” in v1

**How to enable:** set `automation_enabled=false`

### C) Reduced tokens mode
**What it does:**
- Lowers `max_output_tokens` and/or input truncation to control latency/cost

**When to use:**
- cost spikes without outright vendor failure

---

## 3) Decision table (triggers → actions)

| Symptom | Likely cause | Immediate action | Follow-up action | Exit criteria |
|---|---|---|---|---|
| Queue age rising; errors low | Worker concurrency too low | Increase worker reserved concurrency by +2 | Re-check in 10 min; repeat once | Queue age returns < 60s |
| Worker throttles high | Reserved concurrency too low OR account concurrency exhausted | Increase reserved concurrency (if safe) OR request quota | Ensure upstream rate limits in place | Throttles near 0 |
| Richpanel 429 spikes | Too many API calls / concurrency too high | Reduce worker concurrency by -2; honor Retry-After | If persists → safe mode | 429 rate < 1% |
| OpenAI timeouts/5xx spike | Vendor degradation | Enter safe mode | Reduce tokens; retry later | Errors < 1% for 15 min |
| DLQ count increasing | Hard failures, malformed payloads, auth issues | Enter safe mode; stop automation | Triage DLQ; patch; replay | DLQ stable/declining |
| Cost spikes (tokens/message p95) | Prompt drift or injection | Disable automation; safe mode | Investigate prompts; tighten input truncation | Cost back within budget |

---

## 4) Concurrency tuning rules (v1)

### Increase concurrency only when:
- queue age is rising **and**
- vendor 429 rates are low **and**
- worker errors are low

**How:**
- raise worker reserved concurrency in small steps (e.g., +2)
- wait at least 10 minutes before further change

### Decrease concurrency when:
- Richpanel 429 increases (respect Retry-After)
- OpenAI 429 or timeouts increase

**How:**
- reduce worker reserved concurrency by -2
- if still failing, enter safe mode

---

## 5) Backlog draining (controlled catch-up)
When backlog exists (planned downtime, vendor outage recovery):
- **Do not** “blast drain” by setting concurrency very high.
- Use the backlog strategy doc:
  - `docs/07_Reliability_Scaling/Backlog_Catchup_and_Replay_Strategy.md`

---

## 6) Exiting degraded mode

Only exit safe mode when:
- queue age < 60s (steady) for 15 minutes
- vendor error rates are normal
- no DLQ growth

Exit steps:
1) Set `safe_mode=false`
2) Keep automation enabled but monitor Tier 0/Tier 2 guardrails closely
3) If issues recur → re-enter safe mode and investigate

---

## 7) Safety invariants (must never be violated)
- **Fail closed:** if any uncertainty, do route-only.
- **Auto-close only for whitelisted, deflection-safe templates (CR-001 adds order-status ETA exception) tickets** (project constraint).
- **Tier 0 always overrides** (chargebacks, fraud, legal, threats).
- **Tier 2 disclosures only** when deterministic match is confirmed.

