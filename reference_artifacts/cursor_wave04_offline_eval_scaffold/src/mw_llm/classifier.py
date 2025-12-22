"""Classifier client that calls the OpenAI Responses API with structured outputs."""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from typing import Any, Dict, Optional

from openai import OpenAI

from .config import ClassifierConfig
from .prompt_loader import load_prompt_sections
from .schema_validation import (
     SchemaValidationError,
     get_schema_dict,
     validate_decision_schema,
)
from .types import ClassificationInput

logger = logging.getLogger(__name__)


def _default_team_for_channel(channel: str) -> str:
     normalized = (channel or "").lower()
     if normalized == "livechat":
         return "LiveChat Support"
     if normalized in {"social", "facebook", "instagram"}:
         return "SocialMedia Team"
     if normalized == "tiktok":
         return "TikTok Support"
     if normalized == "phone":
         return "Phone Support Team"
     return "Email Support Team"


def _fallback_decision(input_payload: ClassificationInput, channel: str) -> Dict[str, Any]:
     destination = _default_team_for_channel(channel)
     features = input_payload.features
     template = "t_unknown_ack" if features and features.has_email else None
     return {
         "schema_version": "mw_decision_v1",
         "language": input_payload.language,
         "primary_intent": "unknown_other",
         "secondary_intents": [],
         "routing": {
             "destination_team": destination,
             "confidence": 0.0,
             "needs_manual_triage": True,
             "tags": ["mw-routing-applied", "mw-model-failure"],
         },
         "automation": {
             "tier": "TIER_1_SAFE_ASSIST",
             "action": "ROUTE_ONLY",
             "template_id": template,
             "confidence": 0.0,
             "requires_deterministic_match": False,
         },
         "risk": {"flags": [], "force_human": True},
         "clarifying_questions": [],
         "notes_for_agent": "Model failure fallback applied.",
     }


class ClassifierClient:
     """Thin wrapper over OpenAI Responses with structured schema validation."""

     def __init__(self, config: Optional[ClassifierConfig] = None, *, client: Optional[OpenAI] = None):
         self.config = config or ClassifierConfig()
         self.schema_dict = get_schema_dict(self.config.schema_name)
         self.prompt_sections = load_prompt_sections(self.config.prompt_path)
         self.client = client if not self.config.enable_mock_mode else None
         if self.client is None and not self.config.enable_mock_mode:
             self.client = OpenAI()
         if self.config.enable_mock_mode:
             logger.warning("Classifier running in offline/mock mode.")

     def _build_user_payload(self, input_payload: ClassificationInput) -> str:
         sections = [
             f"prompt_version={self.config.prompt_version}",
             f"schema_version={self.config.schema_name}",
             "---",
             self.prompt_sections.get("allowed intents (v1)", ""),
             self.prompt_sections.get("destination teams", ""),
             self.prompt_sections.get("templates (allowlist)", ""),
             self.prompt_sections.get("clarifying question ids", ""),
             self.prompt_sections.get("routing rules (defaults)", ""),
             self.prompt_sections.get("automation rules (defaults)", ""),
             "---",
             input_payload.to_prompt(),
         ]
         return "\n".join([segment for segment in sections if segment])

     def classify(self, input_payload: ClassificationInput) -> Dict[str, Any]:
         if self.config.enable_mock_mode:
             return MockClassifierClient().classify(input_payload)

         attempt = 0
         last_error: Optional[Exception] = None
         while attempt <= self.config.max_retries:
             attempt += 1
             try:
                 user_payload = self._build_user_payload(input_payload)
                 logger.info(
                     "Calling classifier",
                     extra={
                         "model": self.config.model_name,
                         "prompt_version": self.config.prompt_version,
                         "schema_version": self.config.schema_name,
                     },
                 )
                 response = self.client.responses.create(
                     model=self.config.model_name,
                     input=[
                         {"role": "system", "content": self.prompt_sections.system},
                         {"role": "user", "content": user_payload},
                     ],
                     response_format={
                         "type": "json_schema",
                         "json_schema": {"name": self.config.schema_name, "schema": self.schema_dict},
                     },
                     timeout=self.config.timeout_seconds,
                 )
                 content = response.output[0].content[0].text  # type: ignore[index]
                 parsed = json.loads(content)
                 return validate_decision_schema(parsed)
             except (json.JSONDecodeError, SchemaValidationError) as exc:
                 last_error = exc
                 logger.error("Classifier schema failure: %s", exc)
             except Exception as exc:  # pragma: no cover - network exceptions
                 last_error = exc
                 logger.error("Classifier call failed: %s", exc)
             if attempt <= self.config.max_retries:
                 continue
         logger.error("Classifier fallback due to error: %s", last_error)
         channel = input_payload.features.channel if input_payload.features else "email"
         fallback = _fallback_decision(input_payload, channel)
         return validate_decision_schema(fallback)


class MockClassifierClient:
     """Offline heuristic classifier used for tests + CI."""

     def __init__(self):
         self.allowed_tier2_intents = {"order_status_tracking", "shipping_delay_not_shipped"}

     def classify(self, input_payload: ClassificationInput) -> Dict[str, Any]:
         text = (input_payload.text or "").lower()
         primary_intent = "unknown_other"
         template_id: Optional[str] = None
         tier = "TIER_1_SAFE_ASSIST"
         action = "ROUTE_ONLY"
         requires_match = False
         tags = ["mw-routing-applied", "mw-mock-output"]
         notes = "Mock classifier decision."

         if "where is my order" in text or "tracking" in text:
             primary_intent = "order_status_tracking"
             template_id = (
                 "t_order_status_verified"
                 if input_payload.features and input_payload.features.deterministic_order_link
                 else "t_order_status_ask_order_number"
             )
             tier = (
                 "TIER_2_VERIFIED"
                 if input_payload.features and input_payload.features.deterministic_order_link
                 else "TIER_1_SAFE_ASSIST"
             )
             action = "SEND_TEMPLATE"
             requires_match = tier == "TIER_2_VERIFIED"
             notes = "Order status heuristic."
         elif "cancel" in text and "subscription" in text:
             primary_intent = "cancel_subscription"
             template_id = "t_cancel_subscription_ack_intake"
             action = "SEND_TEMPLATE"
         elif "damaged" in text or "return" in text:
             primary_intent = "damaged_item"
             template_id = "t_damaged_item_intake"
             action = "SEND_TEMPLATE"
         elif "fraud" in text or "chargeback" in text or "legal" in text:
             primary_intent = "fraud_suspected" if "fraud" in text else "chargeback_dispute"
             template_id = "t_fraud_ack" if primary_intent == "fraud_suspected" else "t_chargeback_neutral_ack"
             tier = "TIER_0_ESCALATION"
             action = "ACK_ONLY"
             notes = "Tier 0 risk detected."

         decision = {
             "schema_version": "mw_decision_v1",
             "language": input_payload.language,
             "primary_intent": primary_intent,
             "secondary_intents": [],
             "routing": {
                 "destination_team": _default_team_for_channel(
                     input_payload.features.channel if input_payload.features else "email"
                 ),
                 "confidence": 0.72,
                 "needs_manual_triage": False,
                 "tags": tags,
             },
             "automation": {
                 "tier": tier,
                 "action": action,
                 "template_id": template_id,
                 "confidence": 0.65,
                 "requires_deterministic_match": requires_match,
             },
             "risk": {
                 "flags": ["OTHER_HIGH_RISK"]
                 if tier == "TIER_0_ESCALATION"
                 else [],
                 "force_human": tier == "TIER_0_ESCALATION",
             },
             "clarifying_questions": [],
             "notes_for_agent": notes[:500],
         }
         return validate_decision_schema(decision)
