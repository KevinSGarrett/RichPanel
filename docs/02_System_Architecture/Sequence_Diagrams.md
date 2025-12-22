# Sequence Diagrams

Last updated: 2025-12-21
Last verified: 2025-12-21 — Added idempotency + kill switch notes.

This file uses Mermaid diagrams to describe key runtime flows.

---

## 1) Inbound message → route to a department/team (ACK-fast + idempotency)

```mermaid
sequenceDiagram
    participant C as Customer
    participant RP as Richpanel
    participant APIG as API Gateway
    participant IN as Lambda Ingress
    participant DDB as DynamoDB (Idempotency/State)
    participant Q as SQS FIFO
    participant WK as Lambda Worker
    participant OAI as OpenAI
    participant RPA as Richpanel API

    C->>RP: Sends message
    RP->>APIG: HTTP Target/Webhook (inbound)
    APIG->>IN: Invoke (request)

    IN->>IN: Normalize payload + compute event_idempotency_key
    IN->>DDB: PutItem (conditional) idempotency[event]
    alt Duplicate event (already exists)
        IN-->>RP: 200 OK (no enqueue)
    else First seen
        IN->>Q: SendMessage (MessageGroupId=conversation_id)
        IN-->>RP: 200 OK (fast)
    end

    Q->>WK: Deliver event
    WK->>DDB: Get/Update conversation_state (optional)
    WK->>OAI: Classify intent + extract entities
    OAI-->>WK: intent + confidence + entities

    WK->>WK: Decide routing + actions (respect kill-switch/shadow-mode)
    WK->>DDB: PutItem (conditional) idempotency[action] (per action)
    WK->>RPA: Apply tags/assignment (idempotent)
    RPA-->>WK: 200 OK
    WK->>DDB: Update state + mark done
```

---

## 2) Order status: verified auto-reply (template-based)

```mermaid
sequenceDiagram
    participant RP as Richpanel
    participant Q as SQS FIFO
    participant WK as Lambda Worker
    participant OAI as OpenAI
    participant RPA as Richpanel API
    participant SHOP as Shopify (optional)

    RP->>Q: inbound event enqueued (already ACKed)
    Q->>WK: deliver
    WK->>OAI: classify + extract entities
    OAI-->>WK: intent=order_status, confidence=high

    alt Richpanel order link exists
        WK->>RPA: Get order linked to conversation
        RPA-->>WK: order details
    else Shopify fallback available
        WK->>SHOP: Lookup order (by email/phone/order#)
        SHOP-->>WK: order details
    else No deterministic match
        WK->>RPA: Post safe-assist message (ask for order #)
        RPA-->>WK: ok
    end

    opt Deterministic match
        WK->>WK: Render template with tracking link/number
        WK->>RPA: Post verified order status message
        RPA-->>WK: ok
    end
```

---

## 3) Rate limit hit (429) → backoff + retry path (simplified)

```mermaid
sequenceDiagram
    participant WK as Worker
    participant RPA as Richpanel API
    participant RQ as Retry Queue
    participant DLQ as Dead Letter Queue

    WK->>RPA: Write action (tag/reply)
    RPA-->>WK: 429 Retry-After: X

    WK->>WK: Honor Retry-After + jitter
    alt Retry budget remains
        WK->>RQ: Re-enqueue with attempt+1
    else Exceeded retry budget
        WK->>DLQ: Send message + error summary
    end
```

