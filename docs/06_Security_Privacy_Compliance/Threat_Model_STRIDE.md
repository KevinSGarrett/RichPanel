# Threat Model (STRIDE) — Richpanel Routing Middleware

Last updated: 2025-12-22

This is a practical STRIDE threat model for v1. It is intentionally concrete: assets, entry points, and mitigations.

---

## 1) System summary
Inbound: Richpanel → HTTP Target/webhook → API Gateway → Ingress Lambda  
Async: Ingress Lambda → SQS FIFO → Worker Lambda  
Outbound: Worker Lambda → OpenAI + Richpanel (+ Shopify) → Richpanel updates + customer replies

---

## 2) Assets to protect
| Asset | Why it matters |
|---|---|
| Customer PII (message text, email, phone, order #, tracking) | privacy + trust + legal exposure |
| Credentials (OpenAI, Richpanel, Shopify, webhook secret) | compromise = spam, data exposure, cost blowups |
| Automation correctness | misroutes or wrong replies cause customer harm |
| Auditability + logs | needed for incident response, but also a major leak vector |
| Routing taxonomy + template IDs | integrity needed to avoid drift |

---

## 3) Entry points / trust boundaries
- Public webhook endpoint (API Gateway)
- Outbound API calls (OpenAI/Richpanel/Shopify)
- Operator actions (changing templates/macros, toggling automation)
- CI/CD pipeline (deploy permissions)

---

## 4) STRIDE analysis (v1)

### S — Spoofing
| Threat | Example | Mitigations |
|---|---|---|
| Spoofed webhook caller | attacker hits webhook endpoint directly | webhook auth (HMAC/header token), WAF, schema validation, rate limiting |
| Stolen API key usage | leaked OpenAI key used externally | Secrets Manager, key rotation, usage alerts/budgets |

### T — Tampering
| Threat | Example | Mitigations |
|---|---|---|
| Payload altered in transit | change ticket_id in body | TLS, HMAC signature option, schema validation |
| Template tampering | someone edits customer-facing copy without review | change control + approvals + template governance |

### R — Repudiation
| Threat | Example | Mitigations |
|---|---|---|
| “We can’t prove what happened” | disputed auto-reply | structured audit logs (metadata), correlation IDs, immutable change log |

### I — Information disclosure
| Threat | Example | Mitigations |
|---|---|---|
| PII leaks in logs | message text logged | redact before logging, restrict access, short retention |
| Wrong customer gets tracking | incorrect match | Tier 2 deterministic match + verifier; fail closed |
| Prompt injection data exfil | user instructs model to reveal secrets | LLM policy gate; never include secrets in prompt; structured outputs |

### D — Denial of service
| Threat | Example | Mitigations |
|---|---|---|
| Webhook flood | high QPS hits API | WAF rate limits, auth, fast ack, queue buffering |
| Vendor throttling | OpenAI/Richpanel 429 | backpressure, retries, circuit breaker, route-only safe mode |

### E — Elevation of privilege
| Threat | Example | Mitigations |
|---|---|---|
| Worker role can access too much | wildcard IAM | least-privilege IAM roles, separate env accounts |
| CI/CD can change prod | broad perms | separate deployment role + approvals |

---

## 5) Required security controls (summary)
- webhook auth (best available option)
- idempotency + loop guards
- redaction + logging minimization
- Secrets Manager + rotation
- IAM least privilege + multi-account separation
- safe-mode switch for automation (route-only)
- monitoring for abuse/spikes

See also: `Security_Controls_Matrix.md`.
