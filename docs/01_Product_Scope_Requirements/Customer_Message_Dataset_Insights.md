# Customer Message Dataset Insights (SC_Data)

Last updated: 2025-12-22

You provided `SC_Data_ai_ready_package.zip`, which contains real recent customer conversations and agent responses.
This document summarizes what’s in that dataset **in aggregate** and how we’ll use it to make the project plan more accurate (taxonomy, routing, automation scope, evaluation).

**Important:** This dataset likely contains PII (emails, phone numbers, order numbers, tracking links, addresses).
We will **not** copy/paste raw transcripts into documentation. Any examples must be sanitized or synthetic.

---

## 1) What’s inside the package
The package is “AI-ready” and includes:
- `SC_Data_ai_ready.sqlite` (recommended for analysis)
- `messages.csv` / `messages.jsonl` (message-level rows)
- `conversations_meta.csv` (conversation-level metadata)
- `conversations_full.csv` (includes transcript + private notes — treat as sensitive)
- `fields.csv` (custom fields / form values)
- `conversation_tags.csv` (normalized tags)
- `chunks.jsonl` (chunked text for retrieval / embeddings)

---

## 2) Dataset size (high-level)
- Conversations: **3,613**
- Messages: **28,585**

---

## 3) Channel mix (ConversationType)
Top channel types observed:

| ConversationType | Conversations | Share |
|---|---:|---:|
| email | 2,065 | 57.2% |
| email_from_widget | 1,015 | 28.1% |
| tiktok_shop_message | 230 | 6.4% |
| facebook_feed_comment | 192 | 5.3% |
| instagram_message | 51 | 1.4% |
| instagram_comment | 30 | 0.8% |
| facebook_message | 27 | 0.7% |

Data quality note:
- A tiny number of rows have anomalous `ConversationType` values (likely import artifacts). We will filter/ignore these in evaluation.

---

## 4) Strong intent signals in “fields” (structured labels)
Some conversations have structured “field” labels (likely from forms/macros).
These are helpful as **weak labels** for evaluation.

### 4.1 Support field (when present)
- Support field populated for **1,908** conversations
- Top values:
  - Order status: **1,460** (≈ 76.5% of Support-labeled; ≈ 40.4% of all conversations)
  - Cancel order: **170**
  - Troubleshooting: **103**
  - Pre-Order Management: **68**

### 4.2 Shipping field (when present)
- Shipping field populated for **416** conversations
- Top values:
  - Shipping delay: **211** (≈ 50.7% of Shipping-labeled)
  - Missing items: **112** (≈ 26.9% of Shipping-labeled)
  - Incorrect items: **37**
  - Lost package: **28**

### 4.3 Billing / Escalation fields (chargeback signals)
- Billing field populated: **35** conversations
  - Billing → Chargeback: **9**
- Escalation field populated: **10** conversations
  - Escalation → Chargeback: **8**
- Tag signal:
  - `chargeback-inprocess`: **3**

Takeaway:
- Chargebacks are lower-volume but **high-risk** → dedicated queue recommended.

---

## 5) Topic signal (high-level)
Top `Topic` values in the metadata include:
- “Where is my order?” (**503**)
- “Can I cancel my order?” (**83**)
- “How can I update my shipping address?” (**15**)
- “My order shows delivered, but I didn’t receive it” (**5**)

Note: some `Topic` values appear generic (e.g., “Direct Message”) and should not be treated as intents.

---

## 6) Key operational insight: identifiers are often missing in structured form fields
Example:
- “Order Number” field is present only **9** times in `fields.csv`.

Implication:
- We cannot depend on custom fields being filled.
- The middleware must support:
  - extracting identifiers from message text (regex + LLM)
  - fetching conversation/customer info from Richpanel APIs
  - falling back to “ask for order number” (Tier 1) when needed

---

## 6.1 Identifier presence in customer text (regex-based estimates)

To help design deterministic matching and safe fallbacks, we ran **non-invasive regex scans** on customer message text.

**Important notes**
- These are *approximate* (regex-based), not ground-truth labels.
- We scanned **customer** messages only (not agent messages).
- We report only aggregate percentages; no raw values are stored in this repo.

### Presence anywhere in the conversation (any customer message)
- Email-like pattern present in **~6.4%** of conversations
- Phone-like pattern present in **~28.4%** of conversations
- Order-number-like pattern (e.g., `order #12345` or `#12345`) present in **~16.6%** of conversations
- Tracking-number-like pattern present in **~20.1%** of conversations

### Presence in the first customer message only
- Email-like pattern: **~3.6%** of conversations
- Phone-like pattern: **~7.5%** of conversations
- Order-number-like pattern: **~9.5%** of conversations
- Tracking-number-like pattern: **<1%** of conversations

**Implication**
- We should not depend on the customer providing tracking/order numbers in the first message.
- Order status automation should primarily rely on **Richpanel-linked order data** (Shopify integration) or ask for order # as a fallback.


## 7) How we will use SC_Data in this project plan
### 7.1 Validate and refine intent taxonomy (Wave 01 → Wave 04)
- Confirm RoughDraft’s “top FAQs” match what customers actually ask.
- Expand taxonomy for common edge cases (e.g., shipping delay vs missing items vs delivered-not-received).
- Identify ambiguous multi-intent patterns for tie-breaker rules.

### 7.2 Build offline evaluation sets (Wave 04)
We will produce:
- **Golden set**: human-verified labeled examples (small, high quality)
- **Silver set**: weak labels from tags/fields/historical routing
- **Negative set**: low-context messages, attachment-only tickets, spam/bulk traffic

### 7.3 Improve entity extraction requirements (Wave 04 → Wave 05)
From real text we will derive:
- common order-number formats and phrasing
- shipping/tracking phrasing variants
- cues for chargeback/dispute escalation
- when customers include phone/email vs not

---

## 8) Data handling rule (hard requirement)
- Do not paste raw PII into prompts, logs, tickets, or docs.
- Prefer:
  - masking (e.g., `***-***-1234`)
  - hashing identifiers for joining (order/customer IDs)
  - synthetic examples for documentation
