from __future__ import annotations

from mw_llm.policy import PolicyContext, PolicyEngine


def _base_decision():
    return {
        "schema_version": "mw_decision_v1",
        "language": "en",
        "primary_intent": "order_status_tracking",
        "secondary_intents": [],
        "routing": {
            "destination_team": "Email Support Team",
            "confidence": 0.9,
            "needs_manual_triage": False,
            "tags": ["mw-routing-applied"],
        },
        "automation": {
            "tier": "TIER_2_VERIFIED",
            "action": "SEND_TEMPLATE",
            "template_id": "t_order_status_verified",
            "confidence": 0.85,
            "requires_deterministic_match": True,
        },
        "risk": {"flags": [], "force_human": False},
        "clarifying_questions": [],
        "notes_for_agent": "test",
    }


class _DenyingVerifier:
    def verify(self, _input):
        return {
            "schema_version": "mw_tier2_verifier_v1",
            "allow_tier2": False,
            "confidence": 0.5,
            "downgrade_to_tier": "TIER_1_SAFE_ASSIST",
            "reason_code": "CONFLICTING_INTENT",
            "notes": "conflict",
        }


def test_tier0_override_forces_escalation():
    engine = PolicyEngine()
    decision = _base_decision()
    decision["primary_intent"] = "cancel_subscription"
    context = PolicyContext(channel="email", deterministic_order_link=True, tier0_override_reason="keyword:fraud")
    outcome = engine.apply(decision, context, customer_text="fraud alert")
    assert outcome.decision["automation"]["tier"] == "TIER_0_ESCALATION"
    assert any(event["gate"] == "tier0_override" for event in outcome.gate_report)


def test_tier2_downgraded_without_deterministic_match():
    engine = PolicyEngine()
    decision = _base_decision()
    context = PolicyContext(channel="email", deterministic_order_link=False)
    outcome = engine.apply(decision, context, customer_text="where is my order")
    assert outcome.decision["automation"]["tier"] == "TIER_1_SAFE_ASSIST"
    assert outcome.tier2_attempted and not outcome.tier2_allowed


def test_tier2_verifier_can_deny_even_when_policy_passes():
    engine = PolicyEngine(tier2_client=_DenyingVerifier())
    decision = _base_decision()
    context = PolicyContext(channel="email", deterministic_order_link=True)
    outcome = engine.apply(decision, context, customer_text="where is my order but also cancel it")
    assert outcome.decision["automation"]["tier"] == "TIER_1_SAFE_ASSIST"
    assert not outcome.tier2_allowed
    assert any(event["gate"] == "tier2_verifier" for event in outcome.gate_report)


def test_tier3_disabled_downgrades():
    engine = PolicyEngine()
    decision = _base_decision()
    decision["automation"]["tier"] = "TIER_3_AUTO_ACTION"
    decision["automation"]["action"] = "SEND_TEMPLATE"
    context = PolicyContext(channel="email", deterministic_order_link=True)
    outcome = engine.apply(decision, context, customer_text="order status")
    assert outcome.decision["automation"]["tier"] == "TIER_1_SAFE_ASSIST"
