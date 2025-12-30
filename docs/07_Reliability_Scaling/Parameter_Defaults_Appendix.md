# Parameter Defaults Appendix (v1)

Last updated: 2025-12-22  
Status: **Final (Wave 07)**

This appendix captures the **v1 default runtime parameters** for reliability and scaling.

**Canonical source of truth:** `docs/07_Reliability_Scaling/parameter_defaults_v1.yaml`

This markdown is a human-friendly summary of the defaults and *why* they exist.

---

## 1) Design intent
These defaults are designed to:
- ACK webhooks quickly (do not block on OpenAI / Richpanel / Shopify calls)
- protect downstream services from rate-limit storms
- fail closed on automation (route-only is always available)
- keep ops tuning simple (a small set of knobs, with a defined playbook)

---

## 2) High-impact knobs (what matters most)

| Area | Default | Why |
|---|---:|---|
| Worker reserved concurrency | **10** | Enough headroom for peak + surge while protecting vendors |
| FIFO batch size | **1** | Preserves per-conversation ordering; simplest correctness |
| Visibility timeout | **180s** | Gives time for long vendor calls + retries without dupes |
| Max receives before DLQ | **5** | Prevent infinite retry loops; forces triage |
| Max attempts (app-level) | **3** | Prevent runaway cost/latency; DLQ on repeated failures |
| OpenAI timeout | **30s** | Bound worst-case latency; route-only fallback when exceeded |
| Richpanel timeout | **10s** | Fail fast; respect Retry-After; avoid webhook pileups |
| Shopify enabled | **false** | v1 default until credentials/scopes confirmed |
| Automation enabled | **true** | Allows auto-replies when policy gates allow |
| Safe mode | **false** | When true: **route-only**, no customer-facing replies |

---

## 3) Degraded modes (defaults)

Degraded modes are the *primary reliability tool* when vendors degrade or queues back up.

See: `docs/07_Reliability_Scaling/Tuning_Playbook_and_Degraded_Modes.md`

### Default triggers (guidance)
- **Queue age (oldest message) > 120s for 5 minutes** → enter **safe mode** (route-only)
- **Richpanel 429 spike** → reduce worker concurrency; if persistent, enter safe mode
- **OpenAI timeouts/errors spike** → enter safe mode; optionally reduce max_output_tokens
- **Cost spike / token runaway** → disable automation (`automation_enabled=false`) until investigated

---

## 4) Retry + backoff schedule (v1)
For retryable errors (429/5xx/timeouts), use jittered backoff:
- attempt 1: **2–5s**
- attempt 2: **10–20s**
- attempt 3: **60–120s**

Always honor `Retry-After` if present.

---

## 5) DLQ expectations
The DLQ is not a failure; it is a **control surface**.

- DLQ should stay near **0** in steady state.
- Any sustained DLQ > 0 should trigger triage and/or safe mode.

Replay strategy is documented in:
- `docs/07_Reliability_Scaling/Backlog_Catchup_and_Replay_Strategy.md`

---

## 6) How to tune (summary)
Do not change multiple knobs at once.

Recommended order:
1) Fix downstream 429s/timeouts first (reduce concurrency; honor Retry-After)
2) Increase worker reserved concurrency gradually (e.g., +2)
3) Only then consider queue parameter changes (visibility timeout, retention)

---

## 7) Items intentionally left configurable
- API Gateway rate/burst limits (will vary by tenant behavior)
- Per-channel real-time vs async latency targets (LiveChat only in v1)
- Shopify fallback enablement

