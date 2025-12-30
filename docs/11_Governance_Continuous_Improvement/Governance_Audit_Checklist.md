# Governance Audit Checklist

Last updated: 2025-12-22

This checklist keeps the system stable over time by catching “silent drift” early.
It is intentionally practical and oriented around **evidence**.

Use this alongside:
- `docs/08_Observability_Analytics/Operator_Quick_Start_Runbook.md`
- `docs/10_Operations_Runbooks_Training/Runbook_Index.md`

---

## Frequency
- **Weekly (10–15 min):** quality + ops quick review
- **Monthly (30–60 min):** full governance audit
- **Quarterly:** strategic review (taxonomy + automation scope)

---

## Weekly quick review (recommended)
- [ ] Review routing accuracy trend and top misroutes (Wave 08 dashboards)
- [ ] Review automation volume, block rate, and “customer rejected/stop” signals
- [ ] Review Tier 0 escalations and confirm **no automation** occurred
- [ ] Review cost trend (tokens/message and total spend)
- [ ] Confirm no backlog/DLQ growth and no vendor 429 storms

---

## Monthly audit (full)

### A) Change control and artifact integrity
- [ ] **Decision Log** entries exist for any policy/behavior changes since last month
- [ ] **Change Log** entries exist for any prompt/template/schema/mapping changes since last month
- [ ] No “out of band” production edits were made to:
  - templates/macros
  - thresholds
  - routing mappings
  - prompts
- [ ] Current production artifact versions match the repo versions (prompts/templates/schemas)
- [ ] Any emergency mitigations (safe_mode/template disables) were either:
  - reverted cleanly, or
  - documented as a deliberate ongoing policy

### B) Quality and drift (routing + automation)
- [ ] Weekly golden-set / eval runs happened (per EvalOps schedule) OR explicitly deferred and documented
- [ ] Drift signals reviewed (intent distribution, confidence distribution, mismatch rates)
- [ ] Misrouting spike thresholds were not exceeded (or have postmortem notes)
- [ ] Multi-intent conflicts are not increasing (priority matrix still holds)
- [ ] Template selection distribution is stable; no single template “runs away” unexpectedly
- [ ] Tier 2 deterministic-match success rate is within expected band (no increase in “ask for order #” if it should be linked)
- [ ] Chargebacks/disputes are consistently routed to the dedicated team

### C) Ops health and scaling posture
- [ ] Queue age p95/p99 is within target range
- [ ] DLQ depth is zero (or actively worked with documented reasons)
- [ ] Worker error rate is stable (no new error class spikes)
- [ ] Reserved concurrency and backpressure settings match `parameter_defaults_v1.yaml` (or are documented overrides)
- [ ] Load testing/soak tests are scheduled after major changes (monthly/quarterly as needed)

### D) Security, privacy, and compliance hygiene
- [ ] Secrets rotation performed on schedule (or documented deferral)
- [ ] No redaction failures observed in logs; no raw message bodies in logs
- [ ] Invalid-token requests are not spiking (possible webhook probing)
- [ ] Kill switch was tested in staging (or simulated) within the last 30 days
- [ ] Retention settings remain correct (DynamoDB TTL, log retention)

### E) Vendor/platform changes
- [ ] Richpanel API changes reviewed (if any) and logged
- [ ] OpenAI model/policy changes reviewed (if any) and logged
- [ ] Shopify integration status confirmed (if used) and rate limits respected

### F) Support Ops adoption
- [ ] Support team is using feedback/override signals as expected (no missing adoption)
- [ ] Macros remain aligned to `templates_v1.yaml` (no copy drift)
- [ ] Training materials remain current (Wave 10 training docs)

---

## Quarterly review (recommended)
- [ ] Review whether new intents are required (taxonomy expansion)
- [ ] Review whether additional FAQs should be automated (scope expansion)
- [ ] Review whether channel scope should expand beyond LiveChat/Email
- [ ] Review whether DR posture should change (single-region → multi-region)
- [ ] Review vendor/infra cost posture and renegotiate/optimize as needed
