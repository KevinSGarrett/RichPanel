# File Changes Summary

## `scripts/claude_gate_review.py` (NEW FILE)
**Lines 1-50 (model selection + risk normalization):**
```
GATE_LABEL = "gate:claude"
RISK_LABEL_RE = re.compile(r"^risk:(R[0-4])(?:$|[-_].+)?$")

MODEL_BY_RISK = {
    "risk:R0": "claude-haiku-4-5-20251015",
    "risk:R1": "claude-sonnet-4-5-20250929",
    "risk:R2": "claude-opus-4-5-20251124",
    "risk:R3": "claude-opus-4-5-20251124",
    "risk:R4": "claude-opus-4-5-20251124",
}
```

**Lines 100-150 (Anthropic API call):**
```
def _anthropic_request(payload: dict, api_key: str) -> dict:
    url = "https://api.anthropic.com/v1/messages"
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST")
    request.add_header("content-type", "application/json")
    request.add_header("x-api-key", api_key)
    request.add_header("anthropic-version", "2023-06-01")

    backoff = 2
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                return json.loads(response.read().decode("utf-8"))
```

**Lines 140-190 (verdict parsing logic):**
```
def _parse_verdict(text: str) -> str:
    match = re.search(r"^VERDICT:\s*(PASS|FAIL)\b", text, re.MULTILINE)
    if match:
        return match.group(1)
    return "FAIL"

def _extract_findings(text: str, max_findings: int):
    lines = text.splitlines()
    findings = []
    ...
```

## `.github/workflows/pr_claude_gate_required.yml`
**Before (comment-only gate):**
```
- name: Validate Claude gate comment
  uses: actions/github-script@v7
  with:
    script: |
      const requiredTitle = "Claude Review (gate:claude)";
      const passPattern = /\bPASS\b/;
      ...
      if (!hasPassComment) {
        core.setFailed(
          'Missing Claude PASS comment. Add a PR comment containing "Claude Review (gate:claude)" and "PASS" to satisfy gate:claude.'
        );
      }
```

**After (API-based gate):**
```
concurrency:
  group: claude-gate-${{ github.event.pull_request.number }}
  cancel-in-progress: true

permissions:
  contents: read
  pull-requests: write
  issues: write

- name: Run Claude gate review
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
    GITHUB_TOKEN: ${{ github.token }}
  run: python scripts/claude_gate_review.py --repo "${{ github.repository }}" --pr-number "${{ github.event.pull_request.number }}"
```

**Key changes:**
- Added `ANTHROPIC_API_KEY` secret usage and API call via `scripts/claude_gate_review.py`.
- Added concurrency to prevent multiple reviews per PR.
- Posts a PR comment with verdict and fails the workflow on FAIL.

## `.github/workflows/seed-secrets.yml`
**Added Shopify token seeding (env + upsert):**
```
DEV_SHOPIFY_ADMIN_API_TOKEN: ${{ secrets.DEV_SHOPIFY_ADMIN_API_TOKEN }}
STAGING_SHOPIFY_ADMIN_API_TOKEN: ${{ secrets.STAGING_SHOPIFY_ADMIN_API_TOKEN }}
PROD_SHOPIFY_ADMIN_API_TOKEN: ${{ secrets.PROD_SHOPIFY_ADMIN_API_TOKEN }}

upsert_secret "$NS/shopify/admin_api_token" "${DEV_SHOPIFY_ADMIN_API_TOKEN:-}"
...
upsert_secret "$NS/shopify/admin_api_token" "${STAGING_SHOPIFY_ADMIN_API_TOKEN:-}"
...
upsert_secret "$NS/shopify/admin_api_token" "${PROD_SHOPIFY_ADMIN_API_TOKEN:-}"
```

## `docs/08_Engineering/CI_and_Actions_Runbook.md`
**Removed (comment-only Claude gate):**
```
When `gate:claude` is present, the PR must include a comment containing:
  - `Claude Review (gate:claude)`
  - `PASS`
This comment is the Claude PASS evidence and must be linked in RUN_REPORT.md.
```

**Added (API-based Claude gate + secrets):**
```
- calls the Anthropic Messages API using `ANTHROPIC_API_KEY`
- posts a PR comment with `CLAUDE_REVIEW: PASS|FAIL`, model, risk, and top findings
- fails the check if verdict is FAIL or the API key is missing
- required secret: `ANTHROPIC_API_KEY` (Actions repo secret)
```
