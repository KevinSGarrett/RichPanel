# Richpanel Reply Paths

Last updated: 2026-01-28  
Status: Canonical

## Overview

Outbound replies must be deterministic and channel-aware to prevent “metadata says sent”
without actual delivery. The middleware selects one of two reply paths and fails closed
when safety gates or allowlists block outbound.

## Channel detection

1. Prefer the channel already present in the envelope payload:
   - `via.channel`, `channel`, or nested `ticket.via.channel`.
2. If missing, fetch the ticket (`GET /v1/tickets/{id}`) and inspect `ticket.via.channel`
   (or `ticket.channel`).
3. If the channel is still unknown, treat it as **non-email** (no `send-message`).

## Email channel path (delivery-critical)

When `channel == email` and outbound is permitted:

1. **Safety gates** must be open: `safe_mode=false`, `automation_enabled=true`,
   `allow_network=true`, `RICHPANEL_OUTBOUND_ENABLED=true`.
2. **Allowlist gate** (prod or configured): if not allowlisted, **no outbound attempt**.
3. **Author id**:
   - Prefer `RICHPANEL_BOT_AUTHOR_ID`.
   - In dev, fallback to `GET /v1/users` with caching.
   - If unresolved, **block outbound** and route to support (do not comment instead).
4. **Send**: `PUT /v1/tickets/{id}/send-message` with `author_id` + body.
5. **Verify**: fetch the ticket and confirm the latest comment has `is_operator=true`.
6. **Close**: update ticket status/state (after verification succeeds).
7. **Tag**: apply loop-prevention + reply tags (including `mw-outbound-path-send-message`).

## Non-email channel path (chat/widget/etc.)

When `channel != email`:

1. Apply the same safety and allowlist gates (fail closed if blocked).
2. **Do not call** `/send-message`.
3. Post the reply + close using `PUT /v1/tickets/{id}` with a comment payload.
4. Apply tags (including `mw-outbound-path-comment`).

## Safety behavior summary

- **Outbound blocked** (flags/allowlist/network): no outbound send attempts are made.
- **Allowlist required** (prod or configured): missing/blocked email fails closed,
  even for non-email channels, to prevent unintended external delivery.
- **Unknown channel**: treated as non-email (comment path only).
