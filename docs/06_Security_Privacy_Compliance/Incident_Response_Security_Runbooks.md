# Incident Response — Security Runbooks (v1)

Last updated: 2025-12-22

This file defines minimum runbooks for security/privacy incidents for the Richpanel middleware.

**Core principle:** contain quickly, fail closed (route-only), then investigate.

Related:
- Kill switch / safe mode: `Kill_Switch_and_Safe_Mode.md`
- Logging (PII-safe): `Logging_Metrics_Tracing.md`
- Secrets: `Secrets_and_Key_Management.md`
- Monitoring/alarms: `Security_Monitoring_Alarms_and_Dashboards.md`
- Webhook rotation: `Webhook_Secret_Rotation_Runbook.md`
- Break-glass: `IAM_Access_Review_and_Break_Glass.md`

---

## 1) Incident types covered (v1)
- suspected **API key leak** (OpenAI, Richpanel, Shopify)
- suspected **webhook compromise** (spoofing, replay, abuse)
- suspected **PII leak** (logs, evaluation datasets, alerts)
- automation sending **wrong replies** at scale (bug / drift)
- vendor incident (OpenAI/Richpanel outage or breach notice)

---

## 2) First 10 minutes checklist (always)

1) **Stop customer harm**
   - If there is any risk of wrong disclosures or spam:
     - set `automation_enabled=false`
     - set `safe_mode=true`
   - Verify automation is stopped (metrics + sampling)

2) **Stabilize the system**
   - Check DLQ depth and error rates
   - Ensure routing still functions (if safe)

3) **Preserve evidence**
   - Do not delete logs
   - Capture:
     - a time window (start/end)
     - relevant correlation IDs
     - config flag states

4) **Notify stakeholders**
   - Support Ops + Engineering owner
   - Leadership for customer-impact incidents

---

## 3) Runbook: suspected key leak (OpenAI / Richpanel / Shopify)

**Symptoms**
- Unexpected vendor usage spikes
- Vendor console shows suspicious activity
- Secret appears in logs or repo

**Contain**
1) Disable automation (`automation_enabled=false`) if customer impact possible
2) Rotate/revoke the affected key in vendor console immediately
3) Update Secrets Manager with the new key
4) Deploy/reload service (if needed) to pick up new secret
5) Confirm old key no longer works

**Eradicate**
- Identify leak source:
  - code committed?
  - CI logs?
  - team chat paste?
- Add/strengthen prevention:
  - secret scanning gates
  - least privilege access to secrets

**Recover**
- Re-enable safe mode only after verification:
  - vendor calls succeed with new key
  - no suspicious traffic continues

---

## 4) Runbook: webhook abuse / spoofing

**Symptoms**
- Spike in webhook auth failures (401)
- Spike in ingress requests / WAF blocks
- Duplicate actions or spam-like behavior

**Contain**
1) Turn on safe mode (route-only) if automation could be triggered
2) Increase API throttling temporarily
3) If WAF is enabled:
   - tighten rate-based rule thresholds
4) Rotate webhook token (if using static token)
5) Review logs for:
   - source IP patterns
   - repeated ticket_ids

**Recover**
- Restore normal thresholds after attack subsides
- Add additional protection:
  - WAF in prod (if deferred)
  - HMAC auth if tenant supports

---

## 5) Runbook: PII leak (logs / datasets / alerts)

**Symptoms**
- PII appears in CloudWatch logs
- Someone reports an exported dataset contains raw PII
- Monitoring shows unexpected payload logging

**Contain**
1) Enable safe mode (optional — depends on cause)
2) Stop the logging path (hotfix or config if available)
3) Restrict access to affected log groups/buckets

**Eradicate**
- Find root cause:
  - redaction missed a pattern?
  - debug logging accidentally enabled?
- Patch redaction and add regression tests

**Recover**
- Rotate any exposed secrets (if included)
- Document exposure scope and notify stakeholders

---

## 6) Runbook: wrong replies / wrong disclosures

**Symptoms**
- Customers reply “wrong order”, “not my order”, “stop messaging”
- Support reports auto replies are incorrect
- Spike in escalations after automation

**Contain (immediate)**
1) `automation_enabled=false`
2) `safe_mode=true`
3) Disable specific template(s) if the issue is isolated

**Diagnose**
- Identify which template_id/intents are failing
- Determine if deterministic-match gate failed or verifier logic bug exists
- Check if a Richpanel/Shopify order linking issue is causing mismatch

**Recover**
- Fix root cause
- Run offline eval regression gates
- Re-enable automation gradually (template-by-template)

---

## 7) Vendor outage (OpenAI / Richpanel / Shopify)

**Symptoms**
- Elevated 5xx/429
- Timeouts, long latencies
- Backlog grows (SQS age rising)

**Contain**
1) Turn on safe mode (route-only)
2) Lower concurrency caps
3) Increase backoff/jitter

**Recover**
- Restore automation only after:
  - error rates normalize
  - backlog drains
  - DLQ is empty or handled

---

## 8) Post-incident requirements (v1)

- Write an incident summary:
  - what happened
  - customer impact
  - timeline
  - root cause
  - corrective actions
- Add a regression test or monitoring rule that would catch it earlier next time.
- Update the Decision Log / Risk Register if a new class of risk is discovered.
