# System Matrix (Component Map)

Last verified: 2025-12-29 — Wave F06.

This matrix is a **component-level map** of the system:
- what the component does
- where its canonical documentation lives
- where its code lives (planned until build mode)
- where evidence/runbooks live

This is a **living doc**. Update it whenever components or interfaces change.

---

## Component matrix

| Component | Purpose | Canonical docs | Planned code location | Observability | Security/privacy |
|---|---|---|---|---|---|
| Ingress (Webhook Receiver) | Receive Richpanel webhook events; validate; ACK-fast; enqueue | `docs/03_Richpanel_Integration/Webhooks_and_Event_Handling.md` | `backend/` (planned: `backend/src/ingress/`) | Structured logs; request IDs; enqueue metrics | Signature/auth validation; rate limits; PII minimization |
| Queue (SQS FIFO + DLQ) | Durable buffering; retry/backpressure; poison message isolation | `docs/07_Reliability_Scaling/Retry_Backpressure_and_DLQ.md` | `infra/` (CDK queues) | Queue depth, age-of-oldest, DLQ rate | Least-privilege IAM; encryption at rest; retention controls |
| Worker (Event Processor) | Consume queued events; normalize; call router/automation; write audit | `docs/02_System_Architecture/Data_Flow_and_Components.md` | `backend/` (planned: `backend/src/worker/`) | Per-stage timings; error metrics | PII redaction before logs; idempotency guards |
| Router (LLM intent + dept) | Classify intent; choose department/automation; enforce confidence gates | `docs/04_LLM_Design_Evaluation/LLM_Routing_Taxonomy.md` | `backend/` (planned: `backend/src/router/`) | Confidence distribution; fallback rate | Prompt injection defense; safe fallback; minimal data to LLM |
| FAQ Automation | Generate responses for known FAQs/order status; otherwise escalate | `docs/05_FAQ_Automation/FAQ_Automation_Spec.md` | `backend/` (planned: `backend/src/automation/faq/`) | Success rate; “needs human” rate | Guardrails against hallucination; PII-safe templating |
| Richpanel API Client | Read/update tickets, tags, assignments as allowed | `docs/03_Richpanel_Integration/Richpanel_API_Usage.md` | `backend/` (planned: `backend/src/integrations/richpanel/`) | API latency; error rates; retries | Token/secret handling via AWS Secrets Manager |
| State Store (Idempotency + routing state) | Track event/ticket state; prevent dupes; maintain audit trail | `docs/02_System_Architecture/Data_Model_and_State.md` | `backend/` + `infra/` (DynamoDB) | Read/write latency; throttles | Data retention; access control; encryption |
| Observability & Audit | Dashboards, traces, audit trail, drift monitoring | `docs/08_Observability_Analytics/README.md` | `backend/` + `infra/` | Metrics + tracing + dashboards | Log redaction; access-limited dashboards |
| Operations (Runbooks) | On-call procedures; incident response; playbooks | `docs/10_Operations_Runbooks_Training/Runbook_Index.md` | N/A | N/A | N/A |

---

## Key living doc links

- API surfaces: `docs/04_API_Contracts/API_Reference.md` and `docs/04_API_Contracts/openapi.yaml`
- Config: `docs/09_Deployment_Operations/Environment_Config.md` and `config/.env.example`
- Test evidence: `docs/08_Testing_Quality/Test_Evidence_Log.md` and `qa/test_evidence/`
- Security: `docs/06_Security_Privacy_Compliance/README.md`

