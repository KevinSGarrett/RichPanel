# Response Templates and Tone Guide

Last updated: 2025-12-22  
Status: **Final (Wave 05 closeout)**

## Purpose
Ensure all automated (and agent) responses:
- match your brand voice
- are consistent across channels
- avoid unsafe disclosures and commitments
- reduce follow-up back-and-forth by requesting the right info up front

This guide is written for:
- template writers (Wave 05)
- prompt designers (Wave 04/05)
- human agents using macros
- QA reviewers

---

## Brand voice (recommended default)
Based on your current macros snapshot (Richpanel setup export), the dominant tone is:
- friendly and calm
- concise but not cold
- action-oriented (“please reply with…”, “we’ll help with next steps”)
- avoids heavy formality

**Suggested voice anchors**
- Warm greeting (use first name if available and safe)
- Acknowledge the issue
- Provide the next step(s)
- Close with a simple “reply here” CTA
- Consistent signature: “— Scentiment Support”

---

## Channel guidelines

### Live chat / Messenger
- Prefer 1–3 short lines
- Avoid long bulleted lists unless necessary
- Links are OK, but keep to one primary link if possible
- Do not ask for too many items at once; prioritize order number + one key detail

### Email
- Short paragraphs + bullets are fine
- It’s okay to request multiple items (order # + photos + description)
- Include a clear list of what you need from the customer

### Social / TikTok / public channels
- Avoid order details in public
- Prefer routing to the correct team and requesting the customer move to a private channel
- (Most of this will be “route-only” until verified.)

---

## Safety do’s and don’ts

### Do
- Say what you **know** (from verified data) and label it as “latest update”
- Ask for clarifying info when needed
- Use neutral language when human follow-up is required (“a specialist will review”)
- Remind customers not to share sensitive payment details in screenshots
- Include a path to human support (“reply here”)

### Don’t
- Don’t mention the customer’s full address
- Don’t fabricate shipping timelines or compensation
- Don’t promise refunds/replacements/cancellations (Tier 3 disabled)
- Don’t disclose tracking unless deterministic match is true
- Don’t claim you contacted a carrier/warehouse unless a human did

---

## Approved signatures
Use one consistent signature for automation:
- “— Scentiment Support”

Optional for emails if desired:
- “— Scentiment Support Team”

Avoid automation signing as a specific agent name unless you have a clear “bot” identity strategy in Richpanel.

---

## Tone patterns for tricky situations

### When we need more info
Use: “To make sure we pull up the right order…”  
Avoid: “We can’t find your order.”

### When we can’t do something automatically
Use: “If it has already shipped, we’ll guide you through the best next option.”  
Avoid: “We can’t cancel it.”

### When the customer is upset
- Keep sentences short.
- Acknowledge frustration without mirroring hostility.
- Do not argue; move to steps.

Example:
```text
I’m sorry about that — I know that’s frustrating.

Reply with your order number and we’ll take the next steps right away.
```

---

## Localization
Assumption for v1: **English only**.  
If you have a meaningful Spanish volume, Wave 10 (or a later wave) should add:
- Spanish template variants
- language detection (deterministic, not LLM-only)

---

## Template governance (how we avoid drift)
- Templates used by middleware live in `templates/templates_v1.yaml`.
- Richpanel macros should be aligned to those templates (see `Macro_Alignment_and_Governance.md`).
- Any copy change must be recorded in:
  - Decision Log
  - Change Log
  - Template library update
