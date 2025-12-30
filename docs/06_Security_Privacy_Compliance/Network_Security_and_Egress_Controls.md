# Network Security and Egress Controls (AWS)

Last updated: 2025-12-22

The middleware is primarily serverless. Network controls focus on:
- protecting the public ingress endpoint (API Gateway)
- preventing abuse/spam
- ensuring outbound calls (OpenAI/Richpanel/Shopify) are safe and observable

---

## 1) Ingress protections (API Gateway)

### Required (v1)
- HTTPS only
- API Gateway throttling (rate + burst)
- Request validation (minimal schema) at application layer (ingress lambda)
- Webhook authentication (token/HMAC)
- Structured access logs (PII-safe)

### Recommended (prod)
- Attach AWS WAF to the API Gateway (or put CloudFront + WAF in front)
  - rate-based rule
  - managed rule sets (Common + KnownBadInputs)

### Not recommended for v1
- IP allowlisting: Richpanel IP ranges may change or be unknown.
  - If a stable IP list exists later, we can add an allowlist as an additional layer.

---

## 2) Egress controls (outbound calls)

Outbound calls include:
- OpenAI API
- Richpanel API
- Shopify Admin API (optional)

### Required (v1)
- Strict HTTP client timeouts (connect + read)
- Bounded retries with jitter (respect `Retry-After` for 429s)
- Circuit breaker / safe mode behavior (route-only when vendors are unhealthy)
- Do **not** fetch arbitrary URLs derived from customer messages

### Recommended (v1)
- Maintain an **allowlist** of outbound hostnames in code/config:
  - `api.openai.com`
  - `api.richpanel.com`
  - Shopify admin domain(s) if used
- Reject/ignore any URL that does not match allowlist.

> This is an application-level SSRF defense; it is lightweight and effective for v1.

### Optional (later)
- Place worker lambdas in a VPC and route egress via NAT + egress filtering
- Use AWS Network Firewall or a proxy with strict domain allowlists
- PrivateLink/VPC endpoints for AWS services (SQS/DynamoDB) if lambdas are in VPC

---

## 3) SSRF prevention (required)

**Rule:** never perform HTTP GET/POST to a URL that came from a customer message.

Examples:
- Customers paste “tracking links” or random URLs
- Attackers can embed internal IPs, metadata endpoints, or malicious sites

Allowed behavior:
- We may *display* a tracking link in an outbound customer message **only if** it comes from a trusted source (Richpanel/Shopify), not from customer input.

---

## 4) Observability (required)

- Log outbound vendor calls as metadata only:
  - vendor name
  - endpoint class (e.g., `openai.responses`, `richpanel.order_lookup`)
  - status code
  - latency
  - retry count
- Do not log:
  - request/response bodies
  - secrets
  - full URLs with tokens

---

## 5) “Done” checklist

- [ ] API Gateway throttling configured
- [ ] Webhook auth enforced
- [ ] Ingress schema validation implemented
- [ ] Outbound allowlist enforced
- [ ] Safe mode disables automation on vendor instability
- [ ] WAF enabled in prod (recommended) or explicitly deferred with justification

