import pytest

from mw_llm.schema_validation import (
    SchemaValidationError,
    validate_decision_schema,
    validate_tier2_schema,
)


def test_decision_schema_accepts_valid_payload():
    payload = {
        "schema_version": "mw_decision_v1",
        "language": "en",
        "primary_intent": "order_status_tracking",
        "secondary_intents": [],
        "routing": {
            "destination_team": "Email Support Team",
            "confidence": 0.8,
            "needs_manual_triage": False,
            "tags": ["mw-routing-applied"],
        },
        "automation": {
            "tier": "TIER_1_SAFE_ASSIST",
            "action": "SEND_TEMPLATE",
            "template_id": "t_order_status_ask_order_number",
            "confidence": 0.7,
            "requires_deterministic_match": False,
        },
        "risk": {"flags": [], "force_human": False},
        "clarifying_questions": [],
        "notes_for_agent": "Ready for agent review.",
    }
    assert validate_decision_schema(payload) == payload


def test_decision_schema_rejects_missing_fields():
    payload = {
        "schema_version": "mw_decision_v1",
        "language": "en",
    }
    with pytest.raises(SchemaValidationError):
        validate_decision_schema(payload)


def test_tier2_schema_validation():
    payload = {
        "schema_version": "mw_tier2_verifier_v1",
        "allow_tier2": True,
        "confidence": 0.9,
        "downgrade_to_tier": "TIER_1_SAFE_ASSIST",
        "reason_code": "OK",
        "notes": "Verified.",
    }
    assert validate_tier2_schema(payload) == payload
