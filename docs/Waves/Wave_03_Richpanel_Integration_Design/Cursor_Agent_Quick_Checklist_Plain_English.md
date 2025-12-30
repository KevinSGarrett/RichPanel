# Wave 03 — Cursor Agent Quick Checklist (Plain English)

> **Deferred:** Per owner instruction, this checklist is postponed for now.
> It is not blocking planning. Run it before implementation / before go-live.


Last updated: 2025-12-22

This is the “1-page version” of the Wave 03 verification tasks.

## Why this exists
We want to confirm what your Richpanel workspace supports so we can configure the middleware trigger **correctly the first time** and avoid:
- triggers not firing
- routing fights with legacy automations
- insecure webhooks
- broken payloads due to message-text formatting
- order status automation failing due to missing order links

## What the agent should return
Reply with **YES/NO** + screenshot for each item:

1) **Can we trigger an HTTP Target/webhook from Tagging Rules?**  
2) **If not, can we trigger it from Assignment Rules?**  
3) **Can HTTP Targets include custom headers?** (we want `X-Middleware-Token`)  
4) **If we include message text in the body template, does it stay valid JSON?**  
   - test with quotes + newlines  
5) **Do most tickets have orders linked?**  
   - test 5–10 recent tickets using `GET /v1/order/{conversationId}`  

## “If unknown / not supported” defaults
If any item is “NO”:
- Trigger from **Assignment Rules** (first rule)  
- Put shared secret in **request body** (not header)  
- Send **ticket_id only** (no message text) and fetch via API  
- If order not linked: ask for order # + route to human