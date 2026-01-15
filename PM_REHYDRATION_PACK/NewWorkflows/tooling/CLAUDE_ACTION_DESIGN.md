# Design + implementation guide — Claude review in GitHub Actions

This document shows **two recommended implementation paths** for Claude review:

- **Path 1 (Recommended): Claude Code GitHub Actions**  
  Uses the official Claude Code GitHub Action and GitHub app integration.

- **Path 2 (Custom): Direct Claude API “Semantic Review” workflow**  
  You build a small script that calls the Claude Messages API.

Both paths support your “no human work performed” strategy.

---

## 0) Decision table

| Need | Best choice |
|------|------------|
| Quickest “official” setup, comment-driven (`@claude`) | Path 1 |
| Fully custom JSON output and tight gating logic | Path 2 |
| Want Claude to also implement fixes automatically | Path 1 (but carefully limit permissions) |
| Want Claude to *only* review, never modify code | Path 2, or Path 1 with read-only permissions |

---

# Path 1 — Claude Code GitHub Actions (official)

## 1) Overview

Claude Code GitHub Actions lets Claude respond to `@claude` mentions and/or run in automation mode with a `prompt`, depending on your workflow trigger and configuration.

Key properties:
- runs on GitHub runners (your code stays on your infrastructure)
- uses repository secret `ANTHROPIC_API_KEY`
- supports model selection via CLI args (`claude_args`)

---

## 2) Setup steps (manual)

1) Install the Claude GitHub app for the repository.
2) Add a GitHub Actions secret:
   - `ANTHROPIC_API_KEY`
3) Add a workflow in `.github/workflows/claude-review.yml`.

> Note: A Claude Pro/Max subscription and the Claude API/Console are separate products in many setups; GitHub Actions automation requires an **API key** (`ANTHROPIC_API_KEY`) from the Claude Console.


> If you already use Claude Code in terminal, `/install-github-app` can automate setup.

---

## 3) Recommended workflow: “review on gates:ready”

This workflow runs only when:
- risk is R2+ AND
- `gates:ready` label is present

(Prevents burning tokens on every push.)

```yaml
name: Claude Review (Semantic)

on:
  pull_request:
    types: [labeled, synchronize, opened]

jobs:
  claude_review:
    if: >
      contains(github.event.pull_request.labels.*.name, 'gates:ready') &&
      (
        contains(github.event.pull_request.labels.*.name, 'risk:R2-medium') ||
        contains(github.event.pull_request.labels.*.name, 'risk:R3-high') ||
        contains(github.event.pull_request.labels.*.name, 'risk:R4-critical')
      )
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: "/review"
          claude_args: |
            --max-turns 5
            --model claude-sonnet-4-5-20250929
```

Notes:
- If you want Claude to *only* comment and never change code, keep permissions minimal.
- If you want a stricter prompt, replace `/review` with a custom prompt string or use the CSR prompt from `tooling/CLAUDE_PROMPTS.md`.

---

## 4) Making output enforceable

To make Claude review “machine enforceable”, you want:
- deterministic PASS/FAIL output
- the workflow to fail when verdict is not PASS

Claude Code Action is excellent for interactive review, but strict JSON gating may be easier with Path 2.

---

# Path 2 — Direct Claude API semantic review workflow (custom)

## 1) Overview

You will:
1. Fetch PR diff in GitHub Actions.
2. Call Claude Messages API.
3. Parse response JSON.
4. Post comment and fail workflow when verdict != PASS.

This produces a clean status check (the workflow itself).

---

## 2) API requirements (headers)

When using curl directly, the Claude API expects:
- `x-api-key`
- `anthropic-version`
- `content-type: application/json`

And messages are sent to:
- `POST https://api.anthropic.com/v1/messages`

---

## 3) Recommended workflow: “workflow_dispatch by PR number”

This is closest to how you trigger Bugbot today.

```yaml
name: Claude Review Trigger

on:
  workflow_dispatch:
    inputs:
      pr_number:
        description: "PR number to review"
        required: true
        type: string

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      contents: read
    steps:
      - uses: actions/checkout@v4

      - name: Fetch PR diff
        id: pr
        uses: actions/github-script@v7
        with:
          script: |
            const prNumber = Number(core.getInput('pr_number'));
            const { data: pr } = await github.rest.pulls.get({
              owner: context.repo.owner,
              repo: context.repo.repo,
              pull_number: prNumber,
            });
            const diff = await github.request(pr.diff_url, {
              headers: { accept: 'application/vnd.github.v3.diff' }
            });
            core.setOutput('title', pr.title);
            core.setOutput('diff', diff.data);

      - name: Run Claude semantic review
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          PR_TITLE: ${{ steps.pr.outputs.title }}
          PR_DIFF: ${{ steps.pr.outputs.diff }}
        run: |
          python scripts/claude_semantic_review.py

      - name: Comment results (optional)
        # script posts comment with verdict and stamps the head SHA
```

Your `scripts/claude_semantic_review.py` should:
- truncate/segment large diffs
- inject the CSR prompt template
- parse JSON from Claude
- exit non-zero if verdict != PASS

---

## 4) Stamping for freshness (“review is for this commit”)

To support the staleness rules, your comment should include:

`<!-- claude-review: sha=<HEAD_SHA> run=<RUN_ID> -->`

Your policy-gate workflow can then compare the SHA to current PR head SHA.

---

## 5) Recommended rollout plan

1) Start with workflow_dispatch (manual control) to validate output.
2) Add label-triggered automation for `gates:ready`.
3) Add policy-gate required check to enforce “no merge without required gates”.
4) Tune model + max_tokens to control cost.

