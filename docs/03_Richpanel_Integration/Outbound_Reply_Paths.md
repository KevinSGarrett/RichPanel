# Outbound Reply Paths

## Why two paths exist
- **Middleware comment** (`PUT /v1/tickets/{id}` with `comment`): records an internal note and can close the ticket, but it does not reliably send an outbound email to the customer.
- **Operator reply** (`PUT /v1/tickets/{id}/send-message`): creates a real agent reply that Richpanel delivers over the email channel.

## Path selection
- **Email channel**: use `/send-message` with a valid `author_id`, then close the ticket via the safe update-candidate strategy (no middleware comment).
- **Non-email/unknown channel**: use the existing middleware comment + close flow.

Channel is read from `ticket.via.channel` (lowercased) after a ticket fetch, then falls back to any payload channel. Missing `via` or `channel` falls back to the comment path.

## Author resolution (email channel)
1. Use `RICHPANEL_BOT_AGENT_ID` if set (fallback: `RICHPANEL_BOT_AUTHOR_ID`).
2. Else call `GET /v1/users` and select a stable agent/operator id (role/type contains "agent" or "operator"), or the first user with an id.

Only the selection strategy and a short hash of the id are logged (no names or emails).

**Production guardrail:** When `MW_ENV`/`RICHPANEL_ENV` resolves to `prod` or `production`, `RICHPANEL_BOT_AGENT_ID` (or fallback `RICHPANEL_BOT_AUTHOR_ID`) is required and fallback to `/v1/users` is disabled.

## Tags applied
- Loop prevention + reply success: `mw-auto-replied`, `mw-order-status-answered`, `mw-reply-sent`.
- Path tags for disambiguation:
  - `mw-outbound-path-send-message` for `/send-message`
  - `mw-outbound-path-comment` for middleware comment
- Failure routing uses `route-email-support-team` plus explicit reason tags (for example `mw-send-message-failed` or `mw-send-message-author-missing`).

## Safety gates
All outbound replies remain gated by `safe_mode`, `automation_enabled`, `allow_network`, and `outbound_enabled`. When gates fail, the worker stays read-only and routes to support.

Email-channel replies also enforce a customer allowlist:
- `MW_OUTBOUND_ALLOWLIST_EMAILS` (comma-separated full emails)
- `MW_OUTBOUND_ALLOWLIST_DOMAINS` (comma-separated domains)

Production is deny-by-default unless an allowlist entry matches the customer email.
