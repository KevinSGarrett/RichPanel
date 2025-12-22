"""Application-layer policy gates."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .tier2_verifier import Tier2VerifierClient, MockTier2VerifierClient
from .types import GateEvent, Tier2VerifierInput

TIER0_INTENTS = {
     "chargeback_dispute",
     "legal_threat",
     "harassment_threats",
     "fraud_suspected",
}
TIER0_TEMPLATE = {
     "chargeback_dispute": "t_chargeback_neutral_ack",
     "legal_threat": "t_legal_threat_ack",
     "harassment_threats": "t_harassment_ack",
     "fraud_suspected": "t_fraud_ack",
}
TIER2_ALLOWLIST = {"order_status_tracking", "shipping_delay_not_shipped"}


@dataclass(slots=True)
class PolicyContext:
     channel: str
     deterministic_order_link: bool | None
     tier0_override_reason: Optional[str] = None


@dataclass(slots=True)
class PolicyOutcome:
     decision: Dict[str, Any]
     gate_report: List[Dict[str, Any]]
     tier2_attempted: bool
     tier2_allowed: bool


class PolicyEngine:
     def __init__(self, tier2_client: Optional[object] = None):
         self.tier2_client = tier2_client

     def apply(self, decision: Dict[str, Any], context: PolicyContext, customer_text: str) -> PolicyOutcome:
         mutable = copy.deepcopy(decision)
         gate_report: List[GateEvent] = []

         self._enforce_tier0(mutable, context, gate_report)
         self._disable_tier3(mutable, gate_report)
         tier2_attempted, tier2_allowed = self._enforce_tier2(mutable, context, customer_text, gate_report)

         return PolicyOutcome(
             decision=mutable,
             gate_report=[event.as_dict() for event in gate_report],
             tier2_attempted=tier2_attempted,
             tier2_allowed=tier2_allowed,
         )

     def _enforce_tier0(self, decision: Dict[str, Any], context: PolicyContext, gate_report: List[GateEvent]) -> None:
         primary_intent = decision["primary_intent"]
         risk_flags = decision.get("risk", {}).get("flags", [])
         reason = None
         if primary_intent in TIER0_INTENTS:
             reason = f"model_intent:{primary_intent}"
         elif context.tier0_override_reason:
             reason = context.tier0_override_reason
         elif any(flag in {"CHARGEBACK_DISPUTE", "LEGAL_THREAT", "HARASSMENT_THREATS", "FRAUD_SUSPECTED"} for flag in risk_flags):
             reason = "risk_flags"

         if not reason:
             return

         template = TIER0_TEMPLATE.get(primary_intent, "t_unknown_ack")
         decision["automation"].update(
             {
                 "tier": "TIER_0_ESCALATION",
                 "action": "ACK_ONLY",
                 "template_id": template,
                 "confidence": 0.0,
                 "requires_deterministic_match": False,
             }
         )
         decision["routing"]["destination_team"] = "Chargebacks / Disputes Team"
         decision["routing"]["needs_manual_triage"] = True
         tags = set(decision["routing"].get("tags", []))
         tags.add("mw-tier0-override")
         decision["routing"]["tags"] = list(tags)[:12]
         decision["risk"]["force_human"] = True
         gate_report.append(GateEvent(gate="tier0_override", status="FORCED", reason=reason))

     def _disable_tier3(self, decision: Dict[str, Any], gate_report: List[GateEvent]) -> None:
         if decision["automation"]["tier"] != "TIER_3_AUTO_ACTION":
             return
         decision["automation"].update(
             {
                 "tier": "TIER_1_SAFE_ASSIST",
                 "action": "ROUTE_ONLY",
                 "template_id": None,
                 "requires_deterministic_match": False,
             }
         )
         gate_report.append(GateEvent(gate="tier3_disabled", status="DOWNGRADED", reason="tier3_paused"))

     def _enforce_tier2(
         self,
         decision: Dict[str, Any],
         context: PolicyContext,
         customer_text: str,
         gate_report: List[GateEvent],
     ) -> tuple[bool, bool]:
         is_tier2 = decision["automation"]["tier"] == "TIER_2_VERIFIED"
         if not is_tier2:
             return False, False

         reasons: List[str] = []
         if decision["primary_intent"] not in TIER2_ALLOWLIST:
             reasons.append("intent_not_allowlisted")
         if context.deterministic_order_link is not True:
             reasons.append("missing_deterministic_match")
         if not decision["automation"].get("requires_deterministic_match"):
             reasons.append("requires_flag_false")

         if reasons:
             self._downgrade_to_tier1(decision, reason=";".join(reasons))
             gate_report.append(GateEvent(gate="tier2_policy", status="DOWNGRADED", reason=";".join(reasons)))
             return True, False

         verifier = self.tier2_client
         if verifier is None:
             verifier = MockTier2VerifierClient()

         verifier_input = Tier2VerifierInput(
             deterministic_order_link=context.deterministic_order_link,
             proposed_primary_intent=decision["primary_intent"],
             customer_message=customer_text,
         )
         verifier_result = verifier.verify(verifier_input)
         gate_report.append(
             GateEvent(
                 gate="tier2_verifier",
                 status="ALLOWED" if verifier_result["allow_tier2"] else "DENIED",
                 reason=verifier_result["reason_code"],
             )
         )
         if verifier_result["allow_tier2"]:
             return True, True

         downgrade_target = verifier_result["downgrade_to_tier"]
         reason = verifier_result["reason_code"]
         if downgrade_target == "ROUTE_ONLY":
             decision["automation"].update(
                 {
                     "tier": "TIER_1_SAFE_ASSIST",
                     "action": "ROUTE_ONLY",
                     "template_id": None,
                     "requires_deterministic_match": False,
                 }
             )
         else:
             self._downgrade_to_tier1(decision, reason=reason)
         return True, False

     @staticmethod
     def _downgrade_to_tier1(decision: Dict[str, Any], reason: str) -> None:
         decision["automation"].update(
             {
                 "tier": "TIER_1_SAFE_ASSIST",
                 "action": "SEND_TEMPLATE",
                 "template_id": decision["automation"].get("template_id") or "t_order_status_ask_order_number",
                 "confidence": min(decision["automation"].get("confidence", 0.5), 0.6),
                 "requires_deterministic_match": False,
             }
         )
         decision["routing"]["needs_manual_triage"] = True
