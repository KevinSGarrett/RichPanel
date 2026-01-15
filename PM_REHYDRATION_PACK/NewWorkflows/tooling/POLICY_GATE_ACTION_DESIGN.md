# Design — Policy Gate (“risk-based enforcement without constant gate spam”)

## Why you need this

GitHub branch protection cannot easily say:
- “require Codecov only for high-risk PRs”
- “require Bugbot only sometimes”
- “require Claude review only when label is present”

If you mark Codecov/Bugbot/Claude as required checks, you force them to run on **every** PR update — including tiny commits.

### The fix
Add one required check: **`policy-gate`**

`policy-gate` reads PR labels and enforces:
- which gates must exist
- whether they are fresh enough
- whether waivers are documented

This gives you strict enforcement *without* constant running.

---

## What `policy-gate` verifies

For every PR:

1) Exactly one `risk:*` label exists
2) If risk requires heavy gates:
   - Bugbot evidence exists (comment or stamped artifact)
   - Claude evidence exists (comment/check)
   - Codecov statuses exist or coverage evidence exists
3) If waiver label exists:
   - waiver text exists in PR body (basic heuristics)
4) Staleness:
   - if PR updated after last gate outputs, require rerun

---

## Implementation sketch: GitHub Action workflow

### A) Staleness label workflow

On new commits:
- remove `gates:passed`
- add `gates:stale`

```yaml
name: Gates Staleness

on:
  pull_request:
    types: [synchronize]

jobs:
  mark_stale:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
    steps:
      - uses: actions/github-script@v7
        with:
          script: |
            const pr = context.payload.pull_request;
            const labels = pr.labels.map(l => l.name);
            const add = [];
            const remove = [];
            if (labels.includes('gates:passed')) remove.push('gates:passed');
            if (!labels.includes('gates:stale')) add.push('gates:stale');
            for (const name of remove) {
              await github.rest.issues.removeLabel({ ...context.repo, issue_number: pr.number, name });
            }
            for (const name of add) {
              await github.rest.issues.addLabels({ ...context.repo, issue_number: pr.number, labels: [name] });
            }
```

### B) Policy gate workflow (required check)

```yaml
name: Policy Gate

on:
  pull_request:
    types: [opened, synchronize, reopened, labeled, unlabeled, edited]
  workflow_dispatch:

jobs:
  policy_gate:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: read
      statuses: read
      checks: read
    steps:
      - uses: actions/github-script@v7
        with:
          script: |
            const pr = context.payload.pull_request;
            const labels = pr.labels.map(l => l.name);

            const risks = labels.filter(n => n.startsWith('risk:'));
            if (risks.length !== 1) core.setFailed(`Expected exactly 1 risk label; got: ${risks.join(', ')}`);

            const risk = risks[0];
            const needsHeavy = ['risk:R2-medium','risk:R3-high','risk:R4-critical'].includes(risk);

            if (needsHeavy) {
              // Example: require 'gates:passed' label (or other proof)
              if (!labels.includes('gates:passed')) {
                core.setFailed('Heavy gates required, but gates:passed label is missing.');
              }
            }
```

You can make this more sophisticated by:
- searching PR comments for stamps:
  - `<!-- claude-review: sha=... -->`
  - `<!-- bugbot-reviewed: sha=... -->`
- verifying Codecov check conclusions

---

## Recommended enforcement mode (starting point)

Start strict but simple:

- `policy-gate` requires:
  - exactly one risk label
  - if R2+, require `gates:passed` OR waiver label + waiver text

Then grow sophistication:
- verify actual gate outputs exist and are fresh
- verify Codecov patch status

This lets you ship quickly without overengineering upfront.

