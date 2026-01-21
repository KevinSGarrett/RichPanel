# Making Bugbot + Codecov + Claude “Smarter” via PR Metadata

These tools don’t actually “understand your repo” by magic. They infer intent and correctness from:
- the PR title/body
- the diff context
- the tests + evidence you point them to

This document explains exactly what to write in PR metadata so each tool produces higher-signal output.

---

## 1) Bugbot optimization

Bugbot is strongest when it has **ground truth**:
- what you intended
- what must not regress
- where to look (scope/hotspots)

### A) Write declarative intent (not vibes)
Prefer:
- “Default OFF. Enabled only when `FLAG=true`.”
- “Shadow mode must never issue POST/PUT/PATCH/DELETE.”
- “If context missing, fail-closed and route to Email Support Team.”

Avoid:
- “Should be safe”
- “Probably works”
- “Seems fine”

### B) Invariants are Bugbot’s review checklist
Bugbot can comment on what it thinks is wrong, but invariants tell it what would be *actually wrong* for your feature.

Include invariants like:
- “No PII in artifacts”
- “GET-only HTTP trace”
- “Fail-closed when env flags missing”

### C) Give Bugbot a review map
Add 2–6 bullets under “Please double-check”:
- core files/functions
- edge cases
- safety gates

And 2–6 bullets under “Please ignore”:
- generated registries
- rehydration pack artifacts except specific proof JSONs

This reduces noisy comments on non-critical diffs.

---

## 2) Codecov optimization

Codecov reports missing lines. PR metadata helps you:
- interpret what matters
- fix missing coverage faster

### A) Include “coverage hotspots” in the PR body
In “Results & evidence”, add:

- “Codecov hotspots expected: `backend/src/integrations/openai/client.py` and `llm_reply_rewriter.py`.”
- “New branches added: fallback acceptance path; ensure tests cover both success and fallback.”

This makes the Codecov report easier to act on.

### B) Tie tests to acceptance criteria
In “What changed” or “Test plan”, explicitly link:
- AC → file/function → test file/test name

Example:
- “AC: OpenAI rewrite fallback counts as satisfied → `llm_reply_rewriter.py` → `scripts/test_llm_reply_rewriter.py::test_fallback_counts_as_evidence`”

### C) When Codecov fails, update PR metadata
If patch coverage is red:
- add a short “Codecov plan” section (1–3 bullets) to PR body:
  - which files have missing lines
  - which tests you will add
  - which branches must be covered

This keeps the PR auditable and prevents loops.

---

## 3) Claude gate optimization (risk-tiered)

Claude review quality improves when you supply:
- risk framing
- explicit invariants
- evidence pointers
- reviewer focus (what to verify)

### A) Put the risk rationale in one sentence
Example:
- “`risk:R2` because this changes GPT-5 request payload construction and rewrite gating in order-status automation.”

Avoid:
- “R2 ???”
- “maybe risky”

### B) Put “what would be a failure” in the PR body
Claude can reason about correctness better if you state:
- “If OpenAI call fails, deterministic reply must still be intact.”
- “Fallback must be recorded with `error_class`.”

### C) Avoid metadata mistakes that trigger false FAILs
Common gate failures caused by PR metadata:
- risk label typos
- missing evidence links
- escape-sequence corruption (`\risk`, `\backend`, etc.)
- placeholders (`???`)

Use the minimum score gate (08) to prevent these.

### D) Record the Claude gate audit trail
Claude gate reliability requires the PR body to include:
- the model string used (e.g., `claude-opus-4-5-20251101`)
- the Anthropic response id (or `pending — <link>` until the run completes)

---

## 4) Universal PR-metadata “power moves”

### A) Add a minimal proof snippet (PII-safe)
1–6 lines that prove the claim, e.g.:
```text
openai.routing.llm_called=true, response_id=...
openai.rewrite.rewrite_attempted=true, fallback_used=true
```

### B) Keep “pending” anchored
Always write:
- `CI: pending — <link>`
Not:
- “CI pending”

### C) Use backticks for anything that looks like code
- file paths
- env vars
- commands
- secret names

This avoids parsing confusion.

### D) Include a hidden self-score block
The `PR_QUALITY` HTML comment (08) is not for humans; it is for **process reliability**.
It makes it easy to spot metadata regressions and enforce the 95+ bar.

