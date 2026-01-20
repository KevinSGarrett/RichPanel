# PR Title Scoring Rubric (0–100)

Purpose: ensure PR titles are **high-signal**, **machine-readable**, and consistent enough that Bugbot / Codecov / Claude can quickly infer scope and risk.

Target: meet the minimum thresholds in **08_PR_TITLE_AND_DESCRIPTION_SCORE_GATE.md**.

---

## Title formula (preferred)

Use the most specific version that applies:

### A) Work item / build PR (most common)
`B##: <Outcome> (<primary area>) (risk:R#)`

Examples:
- `B48: Capture OpenAI evidence in GPT-5 order-status proofs (risk:R2)`
- `B41: Fail-closed order-status when context missing (risk:R3)`

### B) Run artifact / evidence PR
`RUN:<RUN_ID> <Outcome> (risk:R#)`

Example:
- `RUN:RUN_20260120_0221Z Order status PASS_STRONG proofs + follow-up routing (risk:R2)`

### C) Docs-only PR
`docs(<tag>): <Outcome> (risk:R0)`

Example:
- `docs(B41): Add secrets + environments single source of truth (risk:R0)`

---

## Category A — Format & required metadata (0–30)

**30 points:** all requirements met.

Requirements:
- [ ] Starts with a recognized prefix: `B##:` or `RUN:` or `docs(...)`
- [ ] Includes a valid risk marker: `(risk:R0)` … `(risk:R4)`
- [ ] Uses consistent casing and punctuation (no random ALL CAPS)
- [ ] No placeholder tokens (`???`, `TBD`, `WIP`, “fix stuff”)
- [ ] No escape-sequence corruption (avoid leading backslashes like `\risk`)

Scoring:
- 0–10: missing prefix and/or missing risk
- 11–20: prefix+risk present but messy/placeholder-y
- 21–30: clean, consistent, fully compliant

**Auto-fail (P0):** missing risk marker for any non-draft PR.

---

## Category B — Specific outcome clarity (0–35)

The title should state **what improved** (not just what changed).

Strong patterns:
- “Harden…”
- “Prevent…”
- “Capture evidence for…”
- “Fail-closed when…”
- “Make <flag> opt-in…”

Weak patterns:
- “Update…”
- “Fix bug…”
- “Changes to…”
- “Cleanup…”

Scoring:
- 0–10: vague / generic
- 11–25: somewhat specific but missing the concrete outcome
- 26–35: outcome is explicit, testable, and directly maps to acceptance criteria

---

## Category C — Scope & subsystem signal (0–20)

A reviewer should know which subsystem is affected **from the title alone**.

Checklist:
- [ ] Mentions the main feature area (e.g., `order-status`, `OpenAI`, `Shopify`, `CI gate`, `secrets`)
- [ ] If it touches safety/security/production gates, signals that (e.g., “read-only”, “fail-closed”, “gate”)

Scoring:
- 0–7: no subsystem signal
- 8–14: subsystem implied but not explicit
- 15–20: subsystem explicit and accurate

---

## Category D — Brevity & scanability (0–10)

- Prefer **~50–90 characters**.
- Avoid stacking multiple clauses unless necessary.

Scoring:
- 0–3: too long or hard to scan
- 4–7: acceptable length
- 8–10: concise and scannable

---

## Category E — Consistency with branch/run naming (0–5)

Checklist:
- [ ] `B##` matches branch naming when used (e.g., `b48-...`)
- [ ] RUN titles use the correct run ID

Scoring:
- 0–2: inconsistent
- 3–5: consistent

---

## Auto-fail conditions (score cannot be ≥95)

If any of these occur, the title is considered **<95** automatically:

- Missing `(risk:R#)` marker
- Contains placeholders (`???`, `TBD`, `WIP`)
- Misleading scope (claims “docs-only” but touches runtime behavior)
- Uses unparseable formatting (escape-sequence corruption, broken markdown)

---

## Examples (approximate scores)

### 98–100
- `B48: Capture OpenAI evidence in GPT-5 order-status proofs (risk:R2)`
- `B41: Fail-closed order-status when context missing (risk:R3)`

### 90–94 (good, but not gate-ready)
- `Ensure GPT-5 order-status proofs capture OpenAI evidence`
  - missing explicit `(risk:R#)` and `B##:` prefix

### <80
- `Fix bug`
- `WIP: update things`
- `TBD`
