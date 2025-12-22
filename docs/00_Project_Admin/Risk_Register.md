# Risk Register

Last updated: 2025-12-22  
Last verified: 2025-12-22 — Wave 06 Update 3 (monitoring + rotation + break-glass docs added).

This is the master list of risks to track throughout planning and execution.

| ID | Risk | Likelihood | Impact | Mitigation | Owner | Status |
|---|---|---:|---:|---|---|---|
| R-001 | Automation loops cause repeated replies / spam | Med | High | Action-level idempotency; `mw-routing-applied` guard; de-dup windows; DLQ + alarms | Engineering | Open |
| R-002 | Webhook spoofing triggers unauthorized routing/automation | Med | High | Webhook auth (HMAC/token), request validation, API throttling, WAF rate-limits (prod) | Engineering | Mitigating |
| R-003 | Duplicate events cause double actions (double replies/tags) | High | Med | Event idempotency keys; bounded retries; “exactly once” at action layer | Engineering | Mitigating |
| R-004 | Order status automation leaks private data (wrong customer) | Low | High | Deterministic match gate + Tier 2 verifier; no address disclosure; fallback to “ask for order #” | Engineering + Support Ops | Mitigating |
| R-005 | LLM misroutes or recommends unsafe automation | Med | High | Policy engine overrides; conservative thresholds; Tier 0 always human; schema validation; eval gates | Engineering | Mitigating |
| R-006 | Vendor rate limits cause backlog and SLA misses | Med | Med | Backpressure, concurrency caps, retry with jitter, DLQ; safe mode route-only | Engineering | Open |
| R-007 | Team/tag mapping drifts (renames/new teams) | Med | Med | Mapping registry; drift monitoring; weekly/quarterly audit; fallback routing | Support Ops + Engineering | Open |
| R-008 | Missing identifiers make order automation ambiguous | High | Med | Only automate with deterministic match; otherwise ask for order #; route to human | Support Ops | Mitigating |
| R-009 | Conflicts with existing Richpanel automations (routing fights) | Med | Med | Guard legacy rules with “tag not present”; disable “reassign even if assigned”; staging tests | Support Ops + Engineering | Open |
| R-010 | Richpanel tenant capability mismatch (headers/templating/trigger placement) | Med | Med | Design fallbacks: minimal payload, token-in-body, API fetch; schedule tenant verification before go-live | PM + Engineering | Open |
| R-011 | PII appears in logs/monitoring or over-shared to vendors | Med | High | Redaction before logging; metadata-only logs; minimize OpenAI inputs; retention limits | Engineering | Mitigating |
| R-012 | Shopify/Richpanel order dependency downtime breaks automation | Med | Med | Safe mode + route-only; retries + DLQ; agent-visible tag; customer-safe fallback templates | Engineering + Support Ops | Open |
| R-013 | Chargebacks/disputes mishandled (financial/legal risk) | Low | High | Dedicated Chargebacks/Disputes team; no auto-close; restricted macros; audit queue | Support Ops + Leadership | Mitigating |
| R-014 | Dataset/eval usage leaks PII in non-prod | Med | High | Redact before storage; access controls; separate non-prod accounts; short retention | Engineering | Open |
| R-015 | Data quality anomalies (bad channel values, malformed messages) | Med | Low | Quarantine unknowns; schema validation; robust parsing; monitoring | Engineering | Open |
| R-016 | Serverless cold starts / concurrency limits cause late routing | Med | Med | Reserved concurrency; tuning; SQS buffering; measure p95/p99 | Engineering | Open |
| R-017 | Single-account deployment increases blast radius | Med | High | Multi-account dev/staging/prod; IAM boundaries; separate secrets/stores | Engineering | Open |
| R-018 | Missing baseline audit logging / budgets reduces visibility | Med | High | CloudTrail in prod; log retention; AWS Budgets alarms; security service enablement | Engineering | Mitigating |
| R-019 | No kill switch leads to prolonged customer harm | Low | High | Runtime kill switch + safe mode flags; runbook drills; alarms for unexpected automation | Engineering | Mitigating |
| R-020 | Insufficient monitoring fails to detect abuse or wrong replies early | Med | High | Insufficient monitoring fails to detect abuse or wrong replies quickly; implement baseline alarms/dashboards (Wave 06 monitoring doc); safe mode kill switch; periodic review | Engineering + Support Ops | Mitigating |

Notes:
- Many risks map directly to `CommonIssues.zip` and are expanded in `docs/90_Risks_Common_Issues/`.