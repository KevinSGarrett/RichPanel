# Secure SDLC and Security Testing Plan (v1)

Last updated: 2025-12-22

This document defines minimum security gates for building and operating the middleware.

---

## 1) Required build-time security gates
1) **Secret scanning** in git + CI (block merges)
2) **Dependency scanning** (known vulnerabilities)
3) **Unit tests** for:
   - webhook auth validation
   - idempotency + dedup
   - policy engine fail-closed behavior
   - redaction correctness
4) **Schema validation tests** (LLM structured outputs)

---

## 2) Required pre-production checks (staging)
- Replay/spoof tests against webhook endpoint
- Rate-limit / backpressure test (simulate burst)
- PII log review (sample logs, ensure redaction)
- “Safe mode” toggle test (force route-only)
- Key rotation drill (at least once)

---

## 3) Operational security
- MFA enforced for AWS and vendor consoles
- Least-privilege IAM
- Change management for:
  - templates/macros
  - routing taxonomy
  - model/prompt versions
- Audit of automation rules in Richpanel (quarterly)

---

## 4) Optional (later)
- Pen-test or third-party review
- Egress firewalling (Network Firewall)
- Formal compliance program (SOC 2)
