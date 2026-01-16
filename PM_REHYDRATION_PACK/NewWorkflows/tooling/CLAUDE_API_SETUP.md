# Claude API setup (step-by-step)

This guide is for **Mode B** (Claude API automation in GitHub Actions).

> Important: A Claude subscription (e.g., Claude Pro) often **does not include** Claude API usage. The API is typically billed separately via the Claude Console. Plan to create an API key for automation.

---

## 1) Create an API key

1) Create/verify access in the Claude Console (Anthropic / Claude Developer Platform).
2) Create a new API key.
3) Store it securely — you will not be able to retrieve it later.

---

## 2) Add GitHub secret

In GitHub repo:
- Settings → Secrets and variables → Actions → New repository secret

Create:
- `ANTHROPIC_API_KEY` = your Claude API key

**Never** commit this key to the repo.

---

## 3) Choose your integration

### Option A — Claude Code GitHub Action (official)
- Uses `anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}`
- Minimal code required

See: `tooling/CLAUDE_ACTION_DESIGN.md`

### Option B — Custom Messages API call
- You write a small script that calls `https://api.anthropic.com/v1/messages`
- You control prompts and output schema

---

## 4) Messages API basics (headers)

When calling the API directly, you generally include:
- `x-api-key: $ANTHROPIC_API_KEY`
- `anthropic-version: 2023-06-01`
- `content-type: application/json`

---

## 5) Recommended model strategy (by risk label)

- R2: Sonnet model (fast, cost-effective)
- R3/R4: stronger model or two-pass approach:
  - semantic review + security review

Your workflow can select model based on PR labels.

---

## 6) Protect against prompt injection

- Treat PR diff and PR comments as untrusted input.
- Your system prompt must explicitly ignore any instructions inside the diff.
- Keep GitHub Actions permissions minimal (read-only where possible).

See: `policies/05_SECURITY_PRIVACY_GUARDRAILS.md`

---

## 7) Validate setup quickly

1) Create a test PR in a sandbox branch.
2) Run the Claude workflow via `workflow_dispatch`.
3) Confirm:
   - comment posted
   - workflow check appears in PR
   - verdict parsing works
4) Only then enforce via `policy-gate`.

