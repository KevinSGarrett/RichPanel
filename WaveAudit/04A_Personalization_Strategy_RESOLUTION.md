# Addendum — Personalization Strategy Resolution (2026-01-10)

The original WaveAudit note `04_Message_Personalization_Strategy.md` recommends **template-only** replies for v1, deferring free-form LLM generation to later.

However, the **core project requirement** (see `../01_CORE_GOALS_AND_FLOW.md`) explicitly requires:

> “send a unique, friendly, personalized reply (generated with OpenAI, with guardrails)”

This addendum resolves the mismatch.

---

## Decision

We will ship “unique custom messages” using a **guardrailed rewrite layer**:

1) The system first produces a deterministic, policy-safe template message containing only verified facts:
   - tracking URL / number, or ETA window
   - standard shipping promise language
2) OpenAI is asked to **rewrite** for tone + uniqueness without altering facts.
3) The output is validated:
   - must not introduce new promises
   - must not contradict the known facts
   - must not include secrets or additional PII
   - must stay within length constraints
4) If validation fails or OpenAI is unavailable → fall back to deterministic template.

---

## Safety posture

- The feature remains **OFF by default**.
- It can be enabled only in explicit, time-boxed DEV proof windows until we trust it.
- All prompts + outputs must be logged safely (no raw inbound ticket bodies stored).

---

## Checklist implications

This decision must be reflected in:
- PLAN_CHECKLIST items (implementation + tests + rollback)
- Department routing / automation docs
- Runbooks (proof window evidence capture)

