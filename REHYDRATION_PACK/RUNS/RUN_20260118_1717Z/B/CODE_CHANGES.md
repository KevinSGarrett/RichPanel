# B41 Code Changes - File Diff Summary

## Modified Files

### 1. backend/src/richpanel_middleware/automation/pipeline.py

**Purpose:** Add order-context gate and handoff tags

**Key Changes:**

**Line 104-148:** Order-context validation helper `_missing_order_context()`
```python
def _missing_order_context(
    order_summary: Optional[Dict[str, Any]],
    envelope: EventEnvelope,
    payload: Dict[str, Any],
) -> List[str]:
    summary = order_summary or {}
    missing: List[str] = []

    order_id = (
        summary.get("order_id")
        or summary.get("id")
        or payload.get("order_id")
        or payload.get("orderId")
        or payload.get("order_number")
        or payload.get("orderNumber")
        or payload.get("id")
    )
    if not _is_valid_order_id(order_id, conversation_id=envelope.conversation_id):
        missing.append("order_id")

    created_at = (
        summary.get("created_at")
        or summary.get("order_created_at")
        or payload.get("created_at")
        or payload.get("order_created_at")
        or payload.get("ordered_at")
        or payload.get("order_date")
    )
    if not created_at:
        missing.append("created_at")

    tracking_present = _tracking_signal_present(summary)
    shipping_method = (
        summary.get("shipping_method")
        or summary.get("shipping_method_name")
        or payload.get("shipping_method")
        or payload.get("shipping_method_name")
        or payload.get("shipping_service")
        or payload.get("shipping_option")
    )
    shipping_bucket = normalize_shipping_method(shipping_method) is not None
    if not tracking_present and not shipping_bucket:
        missing.append("tracking_or_shipping_method" if not shipping_method else "shipping_method_bucket")

    return missing
```

**Line 348-391:** Gate logic in `plan_actions()` (handoff tags + structured logging)
```python
        if routing.intent in {"order_status_tracking", "shipping_delay_not_shipped"}:
            order_summary = lookup_order_summary(
                envelope,
                safe_mode=safe_mode,
                automation_enabled=automation_enabled,
                allow_network=allow_network,
            )
            missing_fields = _missing_order_context(order_summary, envelope, payload)
            if missing_fields:
                reasons.append("order_context_missing")
                reason_tag = _missing_context_reason_tag(missing_fields)
                if routing:
                    extra_tags = [
                        EMAIL_SUPPORT_ROUTE_TAG,
                        ORDER_LOOKUP_FAILED_TAG,
                        ORDER_STATUS_SUPPRESSED_TAG,
                    ]
                    if reason_tag:
                        extra_tags.append(reason_tag)
                    routing.tags = sorted(dedupe_tags((routing.tags or []) + extra_tags))
                    if actions:
                        actions[0]["routing"] = asdict(routing)
                ticket_number = payload.get("ticket_number") or payload.get("conversation_no")
                LOGGER.info(
                    "automation.order_status_context_missing",
                    extra={
                        "event_id": envelope.event_id,
                        "conversation_id": envelope.conversation_id,
                        "ticket_id": envelope.conversation_id,
                        "ticket_number": ticket_number,
                        "order_lookup_result": "missing_context",
                        "missing_fields": missing_fields,
                    },
                )
                return ActionPlan(
                    event_id=envelope.event_id,
                    mode=mode,
                    safe_mode=safe_mode,
                    automation_enabled=automation_enabled,
                    actions=actions,
                    reasons=reasons,
                    routing=routing,
                    routing_artifact=routing_artifact,
                )
```
Rationale: Enforces fail-closed behavior when order context is incomplete.

### 2. backend/src/richpanel_middleware/automation/delivery_estimate.py

**Purpose:** Update fallback wording to avoid false confidence

**Key Changes:**

**Line 232-289:** Updated `build_no_tracking_reply()` function
```python
def build_no_tracking_reply(
    order_summary: Dict[str, Any],
    *,
    inquiry_date: Any,
    delivery_estimate: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Construct a deterministic draft reply for no-tracking order status cases.
    """
    estimate = delivery_estimate or compute_delivery_estimate(
        order_summary.get("created_at") or order_summary.get("order_created_at"),
        order_summary.get("shipping_method") or order_summary.get("shipping_method_name"),
        inquiry_date,
    )

    raw_order_id = order_summary.get("order_id") or order_summary.get("id")
    order_id = str(raw_order_id).strip() if raw_order_id is not None else ""
    has_order_id = bool(order_id) and order_id.lower() not in {"unknown", "your order"}

    if not has_order_id:
        fallback_body = (
            "Thanks for reaching out. We don't have tracking details available yet. "
            "A support agent will follow up shortly."
        )
    else:
        fallback_body = (
            "Thanks for your patience. We don't have tracking updates yet. "
            "We'll send tracking as soon as it's ready."
        )

    return {
        "body": fallback_body.strip(),
        "eta_human": None,
        "bucket": None,
        "is_late": None,
    }
```
Rationale: Avoids claiming "we have order X on file" when order_id is unknown.

### 3. backend/tests/test_order_status_context.py (NEW FILE)

**Purpose:** Test missing vs. full order context paths

**Key Test Cases:**

- **Line 29-50:** `test_missing_order_id_no_reply` (no reply + handoff tags)
- **Line 52-73:** `test_missing_created_at_no_reply` (no reply + handoff tags)
- **Line 75-95:** `test_missing_tracking_and_shipping_method_no_reply` (no reply + handoff tags)
- **Line 97-118:** `test_missing_shipping_method_bucket_no_reply` (no reply + handoff tags)
- **Line 120-137:** `test_full_context_proceeds_normally` (draft reply generated)

### 4. backend/tests/test_delivery_estimate_fallback.py (NEW FILE)

**Purpose:** Validate fallback wording when no tracking and no ETA can be computed

**Key Test Cases:**
- **Line 18-23:** `test_no_tracking_reply_without_order_id`
- **Line 25-30:** `test_no_tracking_reply_with_order_id`

### 5. docs/05_FAQ_Automation/Order_Status_Automation.md

**Purpose:** Document the order-context gate

**Changes:** Added sections explaining required context and suppression behavior.

- **Line 36-40:** Safety constraints: order_id + created_at + tracking/shipping required
- **Line 93-97:** Decision flow: gate behavior + handoff tags

### Modified Test Files (for compatibility)

**scripts/test_pipeline_handlers.py**
- Updated fixtures to include required order context and verify suppression behavior.
- Added `load_tests()` so backend tests are included in coverage runs.
- **Line 80-169:** Added order_id/created_at/shipping_method inputs and missing-context assertions.
- **Line 746-763:** Centralized suite build + backend test discovery for coverage.

**scripts/test_read_only_shadow_mode.py**
- Updated mocked order summary with order_id/created_at/shipping_method for gate compliance.
- **Line 48-57:** Added order context in lookup_order_summary mock.
