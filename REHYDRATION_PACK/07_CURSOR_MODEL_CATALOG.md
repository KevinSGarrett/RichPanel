# Cursor model catalog (authoritative)

Last updated: **2026-01-08**  
Owner: **PM / Rehydration Pack**  
Scope: **Cursor Agent prompts (model + MAX mode + cycle)**

This document exists for one reason: **we must not "forget" what models/modes are available or how we're expected to pick them.**  
If Cursor adds/removes models, update this file first, then update the prompt template if needed.

---

## Required prompt header: model + MAX mode + cycle

Every Cursor Agent prompt MUST start with:

- **Model:** `<exact Cursor model name>`
- **MAX mode:** `ON | OFF`
- **Cycle:** `1× | 2× | 3× | 4×`
  - If Cycle ≥ 2×, list Model 2 / Model 3 / Model 4 (may be same or different).

### Selection policy (must follow)
- **85% = best performance & task efficiency** (primary driver)
- **15% = cost consideration** (secondary driver)

---

## Cursor model choices (as provided)

Use these names **exactly** as they appear in Cursor.

### Models
- Composer 1
- Opus 4.5
- Sonnet 4.5
- GPT-5.1 Codex Max
- GPT-5.1 Codex Max Low
- GPT-5.1 Codex Max High
- GPT-5.1 Codex Max Extra High
- GPT-5.1 Codex Max Medium Fast
- GPT-5.1 Codex Max Low Fast
- GPT-5.1 Codex Max High Fast
- GPT-5.1 Codex Max Extra High Fast
- GPT-5.1 Codex
- GPT-5.1 Codex Low
- GPT-5.1 Codex High
- GPT-5.1 Codex Fast
- GPT-5.1 Codex Low Fast
- GPT-5.1 Codex High Fast
- GPT-5.1 Codex Mini
- GPT-5.1 Codex Mini Low
- GPT-5.1 Codex Mini High
- GPT-5.2
- GPT-5.2 Low
- GPT-5.2 High
- GPT-5.2 Fast
- GPT-5.2 Low Fast
- GPT-5.2 High Fast
- GPT-5.2 Extra High
- GPT-5.2 Extra High Fast
- GPT-5.1
- GPT-5.1 Low
- GPT-5.1 High
- GPT-5.1 Fast
- GPT-5.1 Low Fast
- GPT-5.1 High Fast
- Gemini 3 Flash
- Gemini 3 Pro
- Gemini 2.5 Flash
- Grok Code
- Haiku 4.5
- Opus 4.1 (MAX Only)
- Opus 4 (MAX Only)
- Sonnet 4
- Sonnet 4 1M (MAX Only)
- o3
- o3 Pro (MAX Only)
- GPT-4.1
- GPT-5 Mini
- GPT-5 Nano
- GPT-5 Pro (MAX Only)
- Kimi K2

---

## Mode options

### MAX mode (ON/OFF)
- MAX mode is a **separate toggle** from the model name.
- Some models are listed as **(MAX Only)** — those require MAX mode to be ON.

### Cycle agent count (1×–4×)
- Cycle determines how many sequential "agent cycles" Cursor runs.
- If Cycle ≥ 2×, you can select **additional models** for each cycle.
- Models can be **all the same** or **different per cycle** (e.g., Cycle 2×: one model writes code, second model reviews).

---

## Practical guidance: which model for which work

These are defaults meant to keep us consistent. Adjust only when the task demands it.

### Code changes (backend / scripts / infra)
- Prefer **GPT-5.1 Codex Max High** (MAX mode ON) for implementation.
- Use Cycle 2× when correctness matters:
  - Cycle 1: implement
  - Cycle 2: review + edge cases + test validation

### Docs / runbooks / checklists
- Prefer **Sonnet 4.5** or **GPT-5.2 High Fast**.
- MAX mode OFF is acceptable when the work is purely editorial.

### Fast triage / small diffs
- Prefer **GPT-5.2 Fast** (MAX mode OFF unless complexity spikes).

---

## Anti-drift rule

If you are about to run an agent and you're unsure:
1. **Stop.**
2. Open this file.
3. Copy/paste the model name exactly.
4. Explicitly state MAX mode + cycle at the top of the prompt.
