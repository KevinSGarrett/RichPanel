# Success Metrics and SLAs

Last updated: 2025-12-21
Last verified: 2025-12-21 — Updated with Wave 02 baseline latency targets and “never auto-close” constraint.

This document defines how we will measure success and set operational targets.

---

## 1) Core product metrics (what “good” means)

### 1.1 Routing quality (primary)
- **Routing accuracy:** % of conversations routed to the correct destination team/queue (as defined by our mapping).
- **Misroute rate:** % of conversations that require reassignment by agents.
- **Top confusion pairs:** which destinations are most often confused (e.g., Returns Admin vs Email Support).
- **High-confidence accuracy:** accuracy for decisions where confidence ≥ threshold.
- **Low-confidence deflection:** % of conversations routed to a safe default when confidence is low.

### 1.2 Automation value (secondary)
- **Automation eligibility rate:** % of inbound messages that match a supported FAQ intent.
- **Automation success rate:** % of eligible messages successfully handled by automation (no follow-up needed).
- **Automation fallback rate:** % of eligible messages that fell back to human due to missing identifiers, low confidence, or downstream failure.
- **Avoided agent touches:** estimated reduction in agent messages for the automated intents.

### 1.3 Customer outcomes
- **First response time** (overall and by channel)
- **Time to resolution**
- **CSAT** (if tracked) and **low-CSAT rate**
- **Repeat contact rate** within 7–14 days for the same issue

### 1.4 Operational efficiency
- **Agent messages per conversation** (for top intents — should decrease)
- **Cost per conversation** (OpenAI + infra + third-party API)
- **Queue backlog / age** (SQS oldest message age)

---

## 2) Reliability + latency SLAs (baseline for early rollout)

> These are initial targets. We can tighten once we observe real production latency.

### 2.1 Ingress acknowledgement SLA
- **Ack latency (p95):** < 500 ms
- **Ack latency (p99):** < 1.5 s
- **Ack success rate:** 99.9%+

### 2.2 Decision latency (routing/automation) SLA
**Real-time / near-real-time channels** (**LiveChat only** for v1):
- Note: if you later decide TikTok/social must be treated as real-time, move them into this class.
- **Routing action applied (p95):** < 15 s
- **Auto-reply sent when applicable (p95):** < 25 s
- **p99:** < 60 s

**Asynchronous channels** (email, comments):
- **Routing action applied (p95):** < 60 s
- **Auto-reply sent when applicable (p95):** < 120 s
- **p99:** < 10 min (degraded mode)

### 2.3 Safety constraints (non-negotiable)
- Middleware must **never auto-close** tickets.
- Chargebacks/disputes: **Tier 0** (no automation; route to dedicated team/queue).
- Order status/tracking: disclose tracking only when identity match is deterministic.

---

## 3) Targets for Wave 04/05 evaluation
We will define:
- confusion matrix by destination
- per-intent precision/recall for FAQ detection
- calibration curve for confidence scoring
- regression thresholds for CI (block deploy if degraded)

See:
- `docs/04_LLM_Design_Evaluation/Offline_Evaluation_Framework.md`
- `docs/08_Testing_Quality/LLM_Evals_in_CI.md`

---

## 4) Open items
- Confirm which channels are truly “live” in your context (Wave 03).
- Confirm business timezone to interpret response time metrics (Wave 07).
- Confirm OpenAI budget constraints (Wave 07 cost modeling).
