# Cursor Agent Fix: Ticket Reopen on Customer Follow-Up After Auto-Close

**Repo:** `/home/user/RichPanel`
**Prepared:** 2026-02-22
**Branch to create:** `fix/ticket-reopen-followup` (branch off `main`)
**Risk:** Low — 8 new lines inside an already-isolated guard block. No existing paths modified.

---

> **CONFIDENCE NOTE — READ BEFORE STARTING**
>
> The root cause and code logic are well-understood (90%+ confidence). However, the reopen API
> payload `{"ticket": {"state": "open"}}` has **never been tested in this system** — not in DEV,
> not in PROD. Every proof file from every smoke run (B54, B58, B59, B73, B75…) shows
> `"status_after": "closed"` after customer follow-ups. There is no evidence of automatic
> ticket reopening ever having worked. The manual reopening visible in run logs was a human doing
> it via the RichpanelClient for test-prep purposes only.
>
> **DEV verification of this payload is therefore non-negotiable before PROD deploy.**
> If the API call returns non-200 or the ticket does not become OPEN in the DEV Richpanel
> sandbox, stop — the payload is wrong and the fix must be revised before PROD.

---

> **DEV ENVIRONMENT STATUS — READ BEFORE STARTING**
>
> The DEV AWS environment has **not been deployed to in a long time**. All recent updates
> (B75 auto-close fix, B76–B95, PR #269 verbatim-token work) were deployed to PROD only.
> DEV is running significantly older code — possibly code that predates the B75 auto-close
> fix that caused this bug.
>
> **Do NOT skip the DEV sync step (section 7.0).** Deploying the fix to a stale DEV
> environment will produce meaningless test results — you would be testing the fix on top
> of code that does not match main.

---

## 1. What Is Broken and Exactly Why

### 1.1 The Expected End-to-End Flow

1. Customer sends order-status message → webhook fires → SQS → worker Lambda.
2. Intent classified as `order_status_tracking` or `shipping_delay_not_shipped`.
3. Automated reply sent via `PUT /v1/tickets/{id}/send-message`.
4. Ticket auto-closed via `PUT /v1/tickets/{id}` with `{"ticket": {"state": "closed", "status": "CLOSED"}}`.
5. Tags applied: `mw-auto-replied`, `mw-order-status-answered`, `mw-reply-sent`.
6. **Customer replies again** (follow-up on the now-closed ticket):
   - Richpanel fires a new webhook.
   - Middleware detects `mw-auto-replied` loop-prevention tag.
   - Ticket should be **reopened** so Email Support Team can see it in their queue.
   - No second automated reply should be sent.

Steps 1–5 work correctly. Step 6 **does not reopen the ticket**, so Email Support Team never sees the follow-up because Richpanel only shows OPEN tickets in agent queues.

### 1.2 Root Cause — The Chain of Events

**Pre-B75 (B74 era):** `pipeline.py` was created with 22 close candidates tried sequentially. The Lambda had a 30-second timeout. Calling 22 APIs serially exceeded the timeout, so auto-close was **silently failing**. Tickets stayed OPEN after auto-reply. Customer follow-ups landed on an OPEN ticket — naturally visible to the Email Support Team. This is why follow-ups appeared to work.

**B75 (commit `649cffdd` — "fix auto-close"):**
- Reduced close candidates from 22 → 3.
- Moved `{"ticket": {"state": "closed", "status": "CLOSED"}}` to **first position**.
- Increased Lambda timeout 30s → 60s.
- Auto-close now **succeeds on every ticket** using Richpanel's **hard-close** (`status: CLOSED`).
- Unlike `RESOLVED`, a `CLOSED` ticket in Richpanel does **not** auto-reopen when a customer replies.
- The webhook still fires for customer replies on closed tickets — **but the ticket stays CLOSED**.

**B75 → latest (B76, B79, B83–B95, PR #269):** None of these PRs touched the `followup_after_auto_reply` code path. The E2E smoke test passed because it only checked that routing tags were added — it never verified whether the ticket was reopened.

### 1.3 The Missing Code — Exact Location

**File:** `backend/src/richpanel_middleware/automation/pipeline.py`
**Lines 1676–1684** (current broken state):

```python
        if loop_prevention_tag in (ticket_metadata.tags or set()):
            # Route follow-ups after auto-reply to Email Support Team (no duplicate reply,
            # no escalation). Preserve loop-prevention tag to avoid repeated replies,
            # even if the ticket is already closed.
            result = _route_email_support(
                "followup_after_auto_reply", ticket_status=ticket_status
            )
            result.update(_metadata())
            return result
```

This block detects customer follow-ups and adds routing tags. It **never reopens the ticket**. Routing tags on a CLOSED ticket are invisible to agents.

---

## 2. Exact Code Changes Required

### Change 1 — Add constant near line 100

**File:** `backend/src/richpanel_middleware/automation/pipeline.py`

Find this exact text (around line 95–101):

```
SKIP_RESOLVED_TAG = "mw-skip-order-status-closed"
SKIP_FOLLOWUP_TAG = "mw-skip-followup-after-auto-reply"
SKIP_STATUS_READ_FAILED_TAG = "mw-skip-status-read-failed"
ORDER_LOOKUP_FAILED_TAG = "mw-order-lookup-failed"
ORDER_STATUS_SUPPRESSED_TAG = "mw-order-status-suppressed"
ORDER_LOOKUP_MISSING_PREFIX = "mw-order-lookup-missing"
# Follow-up after auto-reply should route to support without escalation.
```

Replace with (add one line after `ORDER_LOOKUP_MISSING_PREFIX`):

```
SKIP_RESOLVED_TAG = "mw-skip-order-status-closed"
SKIP_FOLLOWUP_TAG = "mw-skip-followup-after-auto-reply"
SKIP_STATUS_READ_FAILED_TAG = "mw-skip-status-read-failed"
ORDER_LOOKUP_FAILED_TAG = "mw-order-lookup-failed"
ORDER_STATUS_SUPPRESSED_TAG = "mw-order-status-suppressed"
ORDER_LOOKUP_MISSING_PREFIX = "mw-order-lookup-missing"
FOLLOWUP_REOPEN_TAG = "mw-followup-reopened"
# Follow-up after auto-reply should route to support without escalation.
```

---

### Change 2 — Add reopen logic around lines 1676–1684

**File:** `backend/src/richpanel_middleware/automation/pipeline.py`

Find this exact block (around lines 1676–1684):

```
        if loop_prevention_tag in (ticket_metadata.tags or set()):
            # Route follow-ups after auto-reply to Email Support Team (no duplicate reply,
            # no escalation). Preserve loop-prevention tag to avoid repeated replies,
            # even if the ticket is already closed.
            result = _route_email_support(
                "followup_after_auto_reply", ticket_status=ticket_status
            )
            result.update(_metadata())
            return result
```

Replace with:

```
        if loop_prevention_tag in (ticket_metadata.tags or set()):
            # If the ticket was hard-closed by the auto-reply automation, reopen it
            # so the Email Support Team can see it in their Richpanel queue.
            # Richpanel only surfaces OPEN tickets; a CLOSED ticket with routing
            # tags is invisible to agents. We reopen when closed and continue to
            # the routing step regardless of reopen success (fail-open).
            if _is_closed_status(ticket_status):
                reopen_response = executor.execute(
                    "PUT",
                    f"/v1/tickets/{encoded_id}",
                    json_body={"ticket": {"state": "open"}},
                    dry_run=not allow_network,
                )
                responses.append(
                    {
                        "action": "reopen_for_followup",
                        "status": reopen_response.status_code,
                        "dry_run": reopen_response.dry_run,
                    }
                )
                if 200 <= reopen_response.status_code < 300 and not reopen_response.dry_run:
                    executor.execute(
                        "PUT",
                        f"/v1/tickets/{encoded_id}/add-tags",
                        json_body={"tags": [FOLLOWUP_REOPEN_TAG]},
                        dry_run=not allow_network,
                    )
            # Route follow-ups after auto-reply to Email Support Team (no duplicate reply,
            # no escalation). Preserve loop-prevention tag to avoid repeated replies.
            result = _route_email_support(
                "followup_after_auto_reply", ticket_status=ticket_status
            )
            result.update(_metadata())
            return result
```

**Why this is safe:**
- `_is_closed_status()` already exists in this file (~line 140). Handles "resolved"/"closed"/"solved" case-insensitively.
- `executor`, `encoded_id`, `responses`, `allow_network`, `FOLLOWUP_REOPEN_TAG` are all in scope at this point.
- `_route_email_support(...)` and `return result` are **unchanged** — execute regardless of reopen outcome.
- If reopen returns non-2xx, routing tags are still applied (fail-open — agents can at least search by tag).
- `dry_run=not allow_network` matches the exact pattern used everywhere else in this function.

---

## 3. New Test File — Complete Content

Create this file at `backend/tests/test_pipeline_followup_reopen.py`.
Copy the entire content below verbatim.

```python
"""
Unit tests for the ticket-reopen behaviour in the followup_after_auto_reply path.

The bug: when a customer replies to a CLOSED ticket, pipeline.py detects the
mw-auto-replied loop-prevention tag and routes to Email Support, but never
reopened the ticket. Agents only see OPEN tickets so the follow-up was lost.

These tests verify that execute_order_status_reply() now issues a reopen call
(PUT /v1/tickets/{id} with state:open) before routing tags when ticket is CLOSED,
and does NOT issue the reopen call when the ticket is already OPEN.
"""
from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault("IDEMPOTENCY_TABLE_NAME", "local-idempotency")
os.environ.setdefault("SAFE_MODE_PARAM", "/rp-mw/local/safe_mode")
os.environ.setdefault("AUTOMATION_ENABLED_PARAM", "/rp-mw/local/automation_enabled")
os.environ.setdefault("CONVERSATION_STATE_TABLE_NAME", "local-conversation-state")
os.environ.setdefault("AUDIT_TRAIL_TABLE_NAME", "local-audit-trail")
os.environ.setdefault("CONVERSATION_STATE_TTL_SECONDS", "3600")
os.environ.setdefault("AUDIT_TRAIL_TTL_SECONDS", "3600")

from richpanel_middleware.automation.pipeline import (  # noqa: E402
    LOOP_PREVENTION_TAG,
    FOLLOWUP_REOPEN_TAG,
    execute_order_status_reply,
    ActionPlan,
)
from richpanel_middleware.integrations.richpanel.client import (  # noqa: E402
    RichpanelExecutor,
    RichpanelResponse,
)
from richpanel_middleware.ingest.envelope import build_event_envelope  # noqa: E402


def _ok_response(dry_run: bool = False) -> RichpanelResponse:
    return RichpanelResponse(
        status_code=200, headers={}, body=b"{}",
        url="https://app.richpanel.com/v1/tickets/test-id", dry_run=dry_run,
    )


def _err_response() -> RichpanelResponse:
    return RichpanelResponse(
        status_code=500, headers={}, body=b'{"error":"internal"}',
        url="https://app.richpanel.com/v1/tickets/test-id", dry_run=False,
    )


def _build_envelope(ticket_id: str = "test-conv-1") -> Any:
    return build_event_envelope({
        "conversation_id": ticket_id,
        "ticket_id": ticket_id,
        "via": {"channel": "email"},
        "message": "Where is my order?",
    })


def _build_plan() -> ActionPlan:
    return ActionPlan(
        routing=mock.MagicMock(intent="order_status_tracking", category="order_status"),
        actions=[{
            "type": "order_status_draft_reply",
            "parameters": {
                "draft_reply": {"body": "Your order will arrive in 1-2 days."},
                "order_summary": {"order_id": "ORD-123"},
            },
        }],
        reasons=[],
    )


def _make_executor(status: str) -> mock.MagicMock:
    executor = mock.MagicMock(spec=RichpanelExecutor)
    payload = {
        "status": status,
        "tags": [LOOP_PREVENTION_TAG, "mw-order-status-answered"],
        "via": {"channel": "email"},
        "customer": {"email": "customer@example.com"},
    }
    get_resp = RichpanelResponse(
        status_code=200, headers={}, body=json.dumps(payload).encode(),
        url="https://app.richpanel.com/v1/tickets/test-conv-1", dry_run=False,
    )

    def side_effect(method: str, path: str, **kwargs: Any) -> RichpanelResponse:
        if method == "GET":
            return get_resp
        return _ok_response()

    executor.execute.side_effect = side_effect
    return executor


def _run(executor: mock.MagicMock, allow_network: bool = True) -> Dict[str, Any]:
    with mock.patch(
        "richpanel_middleware.automation.pipeline.resolve_env_name",
        return_value=("dev", "dev"),
    ):
        return execute_order_status_reply(
            _build_envelope(), _build_plan(),
            safe_mode=False, automation_enabled=True,
            allow_network=allow_network, outbound_enabled=allow_network,
            richpanel_executor=executor,
        )


class FollowupReopenTests(unittest.TestCase):

    def test_reopen_put_called_when_ticket_closed(self) -> None:
        """PUT /v1/tickets/{id} with state:open must be called when ticket is CLOSED."""
        executor = _make_executor("CLOSED")
        _run(executor)

        put_calls = [c for c in executor.execute.call_args_list if c.args[0] == "PUT"]
        reopen_calls = [
            c for c in put_calls
            if "/add-tags" not in c.args[1]
            and c.kwargs.get("json_body", {}).get("ticket", {}).get("state") == "open"
        ]
        self.assertTrue(len(reopen_calls) >= 1, "Expected reopen PUT call but got none")

    def test_reopen_put_is_first_put_call(self) -> None:
        """Reopen must happen before routing tags are added."""
        executor = _make_executor("CLOSED")
        _run(executor)

        put_calls = [c for c in executor.execute.call_args_list if c.args[0] == "PUT"]
        self.assertGreater(len(put_calls), 0)
        first_body = put_calls[0].kwargs.get("json_body", {})
        self.assertNotIn(
            "/add-tags", put_calls[0].args[1],
            "First PUT must be reopen, not add-tags",
        )
        self.assertEqual(first_body.get("ticket", {}).get("state"), "open")

    def test_routing_tags_added_after_reopen(self) -> None:
        """route-email-support-team tag must be added after reopening."""
        executor = _make_executor("CLOSED")
        _run(executor)

        all_tags: List[str] = []
        for c in executor.execute.call_args_list:
            if c.args[0] == "PUT" and "/add-tags" in c.args[1]:
                all_tags.extend(c.kwargs.get("json_body", {}).get("tags", []))

        self.assertIn("route-email-support-team", all_tags)

    def test_followup_reopen_audit_tag_added(self) -> None:
        """mw-followup-reopened audit tag must be applied after successful reopen."""
        executor = _make_executor("CLOSED")
        _run(executor)

        all_tags: List[str] = []
        for c in executor.execute.call_args_list:
            if c.args[0] == "PUT" and "/add-tags" in c.args[1]:
                all_tags.extend(c.kwargs.get("json_body", {}).get("tags", []))

        self.assertIn(FOLLOWUP_REOPEN_TAG, all_tags)

    def test_result_is_followup_not_sent(self) -> None:
        """Return must have sent=False and reason=followup_after_auto_reply."""
        executor = _make_executor("CLOSED")
        result = _run(executor)
        self.assertFalse(result.get("sent"))
        self.assertEqual(result.get("reason"), "followup_after_auto_reply")

    def test_no_reopen_when_ticket_already_open(self) -> None:
        """No reopen PUT when ticket is already OPEN."""
        executor = _make_executor("OPEN")
        _run(executor)

        put_calls = [c for c in executor.execute.call_args_list if c.args[0] == "PUT"]
        reopen_calls = [
            c for c in put_calls
            if "/add-tags" not in c.args[1]
            and c.kwargs.get("json_body", {}).get("ticket", {}).get("state") == "open"
        ]
        self.assertEqual(len(reopen_calls), 0, "No reopen PUT when ticket is already OPEN")

    def test_routing_tags_added_even_when_reopen_fails(self) -> None:
        """Routing tags must still be applied if the reopen PUT returns 500 (fail-open)."""
        executor = mock.MagicMock(spec=RichpanelExecutor)
        payload = {
            "status": "CLOSED",
            "tags": [LOOP_PREVENTION_TAG],
            "via": {"channel": "email"},
        }
        get_resp = RichpanelResponse(
            status_code=200, headers={}, body=json.dumps(payload).encode(),
            url="https://app.richpanel.com/v1/tickets/test-conv-1", dry_run=False,
        )
        call_n = {"n": 0}

        def side_effect(method: str, path: str, **kwargs: Any) -> RichpanelResponse:
            if method == "GET":
                return get_resp
            call_n["n"] += 1
            return _err_response() if call_n["n"] == 1 else _ok_response()

        executor.execute.side_effect = side_effect
        result = _run(executor)

        all_tags: List[str] = []
        for c in executor.execute.call_args_list:
            if c.args[0] == "PUT" and "/add-tags" in c.args[1]:
                all_tags.extend(c.kwargs.get("json_body", {}).get("tags", []))

        self.assertIn("route-email-support-team", all_tags)
        self.assertFalse(result.get("sent"))

    def test_dry_run_reopen_uses_dry_run_true(self) -> None:
        """When allow_network=False, reopen PUT must carry dry_run=True."""
        executor = mock.MagicMock(spec=RichpanelExecutor)
        payload = {
            "status": "CLOSED",
            "tags": [LOOP_PREVENTION_TAG],
            "via": {"channel": "email"},
        }
        get_resp = RichpanelResponse(
            status_code=200, headers={}, body=json.dumps(payload).encode(),
            url="https://app.richpanel.com/v1/tickets/test-conv-1", dry_run=True,
        )
        dry_resp = _ok_response(dry_run=True)

        def side_effect(method: str, path: str, **kwargs: Any) -> RichpanelResponse:
            return get_resp if method == "GET" else dry_resp

        executor.execute.side_effect = side_effect
        _run(executor, allow_network=False)

        put_calls = [c for c in executor.execute.call_args_list if c.args[0] == "PUT"]
        reopen_calls = [
            c for c in put_calls
            if "/add-tags" not in c.args[1]
            and c.kwargs.get("json_body", {}).get("ticket", {}).get("state") == "open"
        ]
        for c in reopen_calls:
            self.assertTrue(
                c.kwargs.get("dry_run"),
                "Reopen PUT must use dry_run=True when allow_network=False",
            )


if __name__ == "__main__":
    unittest.main()
```

---

## 4. Git Workflow

### Step 1 — Set up branch

```bash
cd /home/user/RichPanel
git fetch origin main
git checkout main
git pull origin main
git checkout -b fix/ticket-reopen-followup
```

### Step 2 — Apply both code changes to pipeline.py

Edit `backend/src/richpanel_middleware/automation/pipeline.py`:
- Apply Change 1 (add `FOLLOWUP_REOPEN_TAG` constant, ~line 100)
- Apply Change 2 (add reopen block, ~lines 1676–1684)

### Step 3 — Create the new test file

Create `backend/tests/test_pipeline_followup_reopen.py` with the full content from section 3 above.

### Step 4 — Verify it compiles

```bash
python -m compileall -q backend/src backend/tests
```

Expected: silent (no errors).

### Step 5 — Run new tests

```bash
python -m unittest discover -s backend/tests -p "test_pipeline_followup_reopen.py" -v
```

Expected: 8 tests, all PASS.

### Step 6 — Run full test suite (no regressions)

```bash
python -m unittest discover -s backend/tests -p "test_*.py" -v
python -m unittest discover -s scripts -p "test_*.py" -v
```

Expected: all existing tests still pass.

### Step 7 — Commit

```bash
git add backend/src/richpanel_middleware/automation/pipeline.py
git add backend/tests/test_pipeline_followup_reopen.py

git commit -m "Fix: reopen CLOSED ticket on customer follow-up after auto-close

When a customer replies to a ticket auto-closed by the order-status automation,
the middleware correctly detects the follow-up via the mw-auto-replied tag but
was adding routing tags to a CLOSED ticket without reopening it first. Richpanel
only surfaces OPEN tickets in agent queues, so the Email Support Team never saw
these follow-ups.

Root cause: B75 fixed auto-close by switching to {state:closed, status:CLOSED}
(hard-close). Unlike RESOLVED, CLOSED tickets do not auto-reopen on customer
reply. The followup_after_auto_reply guard was never updated to compensate.

Fix: in execute_order_status_reply(), when the loop-prevention tag is detected
and ticket is CLOSED, issue PUT /v1/tickets/{id} with {ticket:{state:open}}
before routing tags. mw-followup-reopened audit tag added on success. Routing
continues regardless of reopen outcome (fail-open).

No existing functionality changed: auto-close candidates, intent detection,
operator-reply detection, and all existing tests are untouched."
```

### Step 8 — Push

```bash
git push -u origin fix/ticket-reopen-followup
```

---

## 5. Create the Pull Request

```bash
cd /home/user/RichPanel

gh pr create \
  --title "Fix: reopen closed ticket on customer follow-up after auto-close" \
  --base main \
  --body "$(cat <<'PRBODY'
## Summary

- **Bug:** Customer follow-up messages on auto-closed tickets were invisible to Email Support Team — ticket remained CLOSED when routing tags were applied. Richpanel only shows OPEN tickets in agent queues.
- **Root cause:** B75 fixed Lambda timeout by using \`status: CLOSED\` (hard-close). Unlike RESOLVED, CLOSED tickets in Richpanel do not auto-reopen on customer reply. The \`followup_after_auto_reply\` guard detected follow-ups correctly but never reopened the ticket.
- **Fix:** When loop-prevention tag detected + ticket is CLOSED: issue \`PUT /v1/tickets/{id}\` with \`{\"ticket\":{\"state\":\"open\"}}\` before routing tags. Audit tag \`mw-followup-reopened\` applied on success. Routing is fail-open (continues even if reopen fails).

## Files Changed

| File | Change |
|---|---|
| \`backend/src/richpanel_middleware/automation/pipeline.py\` | Add \`FOLLOWUP_REOPEN_TAG\` constant + 16-line reopen block inside existing \`followup_after_auto_reply\` guard |
| \`backend/tests/test_pipeline_followup_reopen.py\` | New: 8 unit tests for all reopen path branches |

## What Is NOT Changed

- Auto-close candidate payloads/ordering — untouched
- Intent detection, routing, order lookup — untouched
- Operator-reply detection block — untouched
- All existing tests remain green

## Risk

\`risk:R1\` — Additive change inside an already-isolated guard block. Fail-open design: routing tags still applied if reopen call fails.

## Test Plan

- [x] New unit tests: 8/8 pass
- [x] Full suite: no regressions
- [ ] DEV E2E smoke: \`python scripts/dev_e2e_smoke.py --followup ...\` — verify \`followup.status_after\` is \`"OPEN"\` in proof JSON
- [ ] Richpanel DEV UI: send customer follow-up on closed ticket → ticket appears OPEN with \`route-email-support-team\` and \`mw-followup-reopened\` tags
PRBODY
)"
```

Wait for all CI checks to go green:
- **CI (validate)** — unit tests, compile sanity, coverage
- **Architecture Boundaries** — import-linter
- **PR Claude Gate Required** — Anthropic API review

---

## 6. Merge to Main

Once all CI checks are green:

```bash
gh pr merge --squash --delete-branch
```

---

## 7. Deploy

> **Order is mandatory: DEV sync → DEV verification → PROD.**
> Do not skip any step. Do not deploy to PROD if DEV verification fails.

---

### 7.0 — Pre-flight: Sync DEV with current `main` (REQUIRED — DEV is stale)

**Why:** DEV AWS has not been deployed to in a long time. All recent code changes — including the
B75 auto-close fix that introduced this bug, and everything since — were deployed to PROD only.
DEV is running old code. If you skip this step and run the smoke test against stale DEV code,
the results are meaningless.

**Do this BEFORE applying or testing the fix:**

1. Go to GitHub → **Actions** → **Deploy Dev Stack**.
2. Click **Run workflow** (top-right of the workflow list).
3. Set **Branch:** `main` (not the fix branch, not any feature branch — `main`).
4. Click the green **Run workflow** button.
5. Watch the run. It may take **5–10 minutes** if the DEV environment has gone dormant or if
   CloudFormation needs to re-provision resources. This is normal after a long gap.
6. Confirm the run ends green with no errors and the CloudFormation outputs table is visible in
   the logs.

**Optional sanity check — verify DEV baseline is alive before adding the fix:**

If you want to confirm DEV is actually processing tickets correctly after the sync (recommended
after a long gap), run a baseline smoke first without `--followup`:

```bash
python scripts/dev_e2e_smoke.py \
  --env dev \
  --region us-east-2 \
  --stack-name RichpanelMiddleware-dev \
  --wait-seconds 120 \
  --profile rp-admin-kevin \
  --scenario order_status \
  --ticket-number <fresh DEV ticket number> \
  --require-outbound \
  --require-openai-routing \
  --require-openai-rewrite \
  --proof-path /tmp/dev_baseline_proof.json
```

Expected result: `"sent": true`, auto-reply received, ticket auto-closed. If this fails, DEV
infrastructure is broken independently of this fix — resolve that first before proceeding.

**How to get a fresh DEV ticket number:**
Log in to the Richpanel DEV sandbox (not PROD). Send a new inbound customer message from a
test customer. The ticket ID will appear in the Richpanel DEV conversation list. Use that
integer ticket ID as `--ticket-number`.

---

### 7.1 — Deploy the fix to DEV

After the PR is merged to `main` and DEV is confirmed synced (step 7.0 above):

1. GitHub → **Actions** → **Deploy Dev Stack**.
2. Click **Run workflow**.
3. Branch: `main`.
4. Click **Run workflow**.
5. Wait for completion (3–8 minutes). Confirm no errors and CloudFormation outputs printed.

This deploys the fix (reopen logic + `FOLLOWUP_REOPEN_TAG`) to the DEV Lambda.

---

### 7.2 — Verify the fix in DEV Richpanel sandbox (CRITICAL GATE — cannot skip)

**Why this is non-negotiable:**
The reopen API payload `{"ticket": {"state": "open"}}` has never been tested in this system.
No proof file from any smoke run has ever shown `"status_after": "OPEN"` for a follow-up.
This DEV test is the **first real live test** of whether Richpanel's API accepts this payload
and actually reopens a closed ticket. If it doesn't work, the fix needs a different payload —
and you need to know that before deploying to PROD.

**Steps:**

1. In the Richpanel **DEV** sandbox, get a fresh DEV ticket number (follow a new inbound message
   through auto-close so the ticket is in `CLOSED` state, or use the smoke test's auto-close
   phase as the setup step).

2. Run the full order-status + followup smoke test against DEV:

```bash
python scripts/dev_e2e_smoke.py \
  --env dev \
  --region us-east-2 \
  --stack-name RichpanelMiddleware-dev \
  --wait-seconds 120 \
  --profile rp-admin-kevin \
  --scenario order_status \
  --ticket-number <fresh DEV ticket number> \
  --require-outbound \
  --require-openai-routing \
  --require-openai-rewrite \
  --followup \
  --proof-path /tmp/followup_reopen_proof.json
```

3. Open `/tmp/followup_reopen_proof.json` and look for:

```json
"followup": {
  "status_after": "OPEN",      <-- MUST be "OPEN"; was always "closed" before fix
  "reply_sent": false,
  "routed_to_support": true
}
```

4. In Richpanel **DEV** UI (sandbox):
   - Ticket status = **OPEN** (not CLOSED, not RESOLVED).
   - Tags present: `route-email-support-team`, `mw-followup-reopened`,
     `mw-skip-followup-after-auto-reply`, `mw-auto-replied`.
   - Ticket is visible in the Email Support Team queue / inbox.

5. In CloudWatch Logs for `/aws/lambda/rp-mw-dev-worker`, confirm the Lambda logged:

```json
{"action": "reopen_for_followup", "status": 200, "dry_run": false}
```

**If any of the above checks fail:**

- `status_after` is still `"closed"` **or** the reopen PUT returns non-200:
  The API payload `{"ticket": {"state": "open"}}` is incorrect for this Richpanel version.
  **Stop. Do NOT deploy to PROD.** Investigate the correct reopen payload — possibilities
  include `{"ticket": {"status": "OPEN"}}`, `{"ticket": {"state": "open", "status": "OPEN"}}`,
  or a different endpoint. Update Change 2 in `pipeline.py`, re-run unit tests, open a new PR,
  and repeat the DEV verification cycle.

- Ticket shows OPEN in proof JSON but is not visible in agent queue:
  The routing or queue assignment may require an additional field. Check Richpanel DEV UI
  carefully and compare with a ticket that was manually opened to see what differs.

---

### 7.3 — Deploy to PROD

**Only after all DEV checks in 7.2 pass without exception.**

1. GitHub → **Actions** → **Deploy Prod Stack**.
2. Click **Run workflow**.
3. Branch: `main`.
4. Click **Run workflow**.
5. Wait for completion. Confirm no errors.

---

## 8. Post-Deploy PROD Verification

Monitor CloudWatch Logs for the worker Lambda (`/aws/lambda/rp-mw-prod-worker`).
When the next real customer follow-up on a closed ticket arrives, look for:

```json
{"action": "reopen_for_followup", "status": 200, "dry_run": false}
```

in the `responses` array of the worker log.

In Richpanel PROD, confirm that the ticket becomes OPEN with the expected tags and is visible in the Email Support Team queue.

---

## 9. Diff Summary (Minimal View)

### `backend/src/richpanel_middleware/automation/pipeline.py`

**Change A — 1 line added after `ORDER_LOOKUP_MISSING_PREFIX` (~line 100):**
```diff
 ORDER_LOOKUP_MISSING_PREFIX = "mw-order-lookup-missing"
+FOLLOWUP_REOPEN_TAG = "mw-followup-reopened"
 # Follow-up after auto-reply should route to support without escalation.
```

**Change B — 16 lines added inside existing `if loop_prevention_tag` block (~line 1676):**
```diff
         if loop_prevention_tag in (ticket_metadata.tags or set()):
-            # Route follow-ups after auto-reply to Email Support Team (no duplicate reply,
-            # no escalation). Preserve loop-prevention tag to avoid repeated replies,
-            # even if the ticket is already closed.
+            # If ticket was hard-closed by automation, reopen it so Email Support Team
+            # can see it in their Richpanel queue (only OPEN tickets are surfaced).
+            if _is_closed_status(ticket_status):
+                reopen_response = executor.execute(
+                    "PUT",
+                    f"/v1/tickets/{encoded_id}",
+                    json_body={"ticket": {"state": "open"}},
+                    dry_run=not allow_network,
+                )
+                responses.append(
+                    {
+                        "action": "reopen_for_followup",
+                        "status": reopen_response.status_code,
+                        "dry_run": reopen_response.dry_run,
+                    }
+                )
+                if 200 <= reopen_response.status_code < 300 and not reopen_response.dry_run:
+                    executor.execute(
+                        "PUT",
+                        f"/v1/tickets/{encoded_id}/add-tags",
+                        json_body={"tags": [FOLLOWUP_REOPEN_TAG]},
+                        dry_run=not allow_network,
+                    )
+            # Route follow-ups after auto-reply to Email Support Team (no duplicate reply,
+            # no escalation). Preserve loop-prevention tag to avoid repeated replies.
             result = _route_email_support(
                 "followup_after_auto_reply", ticket_status=ticket_status
             )
             result.update(_metadata())
             return result
```

### `backend/tests/test_pipeline_followup_reopen.py` — new file (full content in section 3)
