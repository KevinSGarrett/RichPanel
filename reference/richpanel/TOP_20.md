# Richpanel Reference Library — Top 20 Docs

Last updated: 2025-12-29

Use this file when you need the **most likely relevant vendor doc** without browsing hundreds of files.

If you need something not listed here:
- start with `INDEX.md` (topic buckets)
- or use the machine registry: `reference/richpanel/_generated/reference_registry.json`

---
## Richpanel Middleware Documentation (general)

- [Richpanel Middleware Documentation.txt](Non_Indexed_Library/Richpanel Middleware Documentation/Richpanel Middleware Documentation.txt) — Baseline vendor documentation for middleware integrations.
- [Richpanel AI Middleware – Integration.txt](Non_Indexed_Library/Richpanel Middleware Documentation/Richpanel AI Middleware – Integration.txt) — High-level integration overview focused on AI middleware.

## Comprehensive Guide (recommended for implementers)

- [Overview.txt](Non_Indexed_Library/Developing Middleware for Richpanel Comprehensive Guide/Overview.txt) — Start here for the comprehensive guide’s structure + mental model.
- [Acknowledge Quickly.txt](Non_Indexed_Library/Developing Middleware for Richpanel Comprehensive Guide/Receiving the Webhook in Your Middleware/Acknowledge Quickly.txt) — ACK-fast guidance for webhook receivers.
- [Verify the Source.txt](Non_Indexed_Library/Developing Middleware for Richpanel Comprehensive Guide/Receiving the Webhook in Your Middleware/Verify the Source.txt) — Webhook authenticity + security checks.
- [Stability of Webhook Triggers.txt](Non_Indexed_Library/Developing Middleware for Richpanel Comprehensive Guide/Integration Entry Points (Triggers)/Stability of Webhook Triggers.txt) — Webhook trigger stability considerations.
- [Unified Triggers Across Channels.txt](Non_Indexed_Library/Developing Middleware for Richpanel Comprehensive Guide/Integration Entry Points (Triggers)/Unified Triggers Across Channels.txt) — How triggers behave across email/chat/etc.
- [Don’t Re-trigger on API Actions.txt](Non_Indexed_Library/Developing Middleware for Richpanel Comprehensive Guide/Avoiding Automation Loops/Don’t Re-trigger on API Actions.txt) — Avoid loops caused by your own API writes.

## Richpanel Integration Notes (practical patterns)

- [Official Integration Entry Points — Stability.txt](Non_Indexed_Library/Richpanel_Integration/Official_Integration_Entry_Points/Stability.txt) — Official entry points + stability expectations.
- [HTTP Target Payload — Default Payload Content.txt](Non_Indexed_Library/Richpanel_Integration/HTTP Target Payload and Available Fields/Default Payload Content.txt) — What the outgoing payload contains by default.
- [HTTP Target Payload — Including IDs and Deduplication Keys.txt](Non_Indexed_Library/Richpanel_Integration/HTTP Target Payload and Available Fields/Including IDs and Deduplication Keys.txt) — How to carry IDs to dedupe safely.
- [Reliability — Delivery Guarantees for HTTP Targets.txt](Non_Indexed_Library/Richpanel_Integration/Reliability and Retries of HTTP Targets & API Calls/Delivery Guarantees for HTTP Targets.txt) — Retry/guarantee semantics (critical for idempotency).
- [Reliability — Timeouts and Success Codes.txt](Non_Indexed_Library/Richpanel_Integration/Reliability and Retries of HTTP Targets & API Calls/Timeouts and Success Codes.txt) — Correct success/timeout patterns.
- [Preventing Loops — Use A Processed Flag.txt](Non_Indexed_Library/Richpanel_Integration/Automation Rule Interactions & Preventing Loops/Use A Processed Flag.txt) — Best practice for loop prevention using tags/flags.
- [Preventing Loops — Trigger On Customer Message Only.txt](Non_Indexed_Library/Richpanel_Integration/Automation Rule Interactions & Preventing Loops/Trigger On Customer Message Only.txt) — Avoid bot/builder actions from re-triggering automation.

## API basics + limits

- [Getting Started RichPanel API.txt](Non_Indexed_Library/API/Getting_Started_RichPanel_API.txt) — API basics + how to get started.
- [Authentication.txt](Non_Indexed_Library/API/Authentication.txt) — Auth patterns for Richpanel API.
- [Limitations.txt](Non_Indexed_Library/API/Limitations.txt) — Rate limits + platform limitations to design around.

## Event payload examples

- [Sample Order Event.txt](Non_Indexed_Library/Order_Event_Structure/Sample_Order_Event.txt) — Example order event payload for parsing + mapping.

## Common issues

- [Automation loops.txt](Non_Indexed_Library/Common Issues/Automation loops.txt) — Real-world automation loop failure mode patterns.
