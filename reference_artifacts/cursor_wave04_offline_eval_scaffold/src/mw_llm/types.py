"""Common dataclasses for classifier inputs and outputs."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class ClassificationFeatures:
     channel: str
     deterministic_order_link: bool | None
     has_order_number: bool
     has_email: bool
     has_phone: bool
     has_tracking_number: bool
     has_attachments: bool = False

     def as_prompt_block(self) -> str:
         items = [
             f"channel={self.channel}",
             f"deterministic_order_link={self.deterministic_order_link}",
             f"has_order_number={self.has_order_number}",
             f"has_email={self.has_email}",
             f"has_phone={self.has_phone}",
             f"has_tracking_number={self.has_tracking_number}",
             f"has_attachments={self.has_attachments}",
         ]
         return "\n".join(items)


@dataclass(slots=True)
class ClassificationInput:
     text: str
     language: str = "en"
     features: ClassificationFeatures | None = None

     def to_prompt(self) -> str:
         header = self.features.as_prompt_block() if self.features else ""
         return f"{header}\ncustomer_message=\"\"\"{self.text.strip()}\"\"\""


@dataclass(slots=True)
class Tier2VerifierInput:
     deterministic_order_link: bool | None
     proposed_primary_intent: str
     customer_message: str

     def to_prompt(self) -> str:
         return "\n".join(
             [
                 f"deterministic_order_link={self.deterministic_order_link}",
                 f"proposed_primary_intent={self.proposed_primary_intent}",
                 f"customer_message=\"\"\"{self.customer_message.strip()}\"\"\"",
             ]
         )


@dataclass(slots=True)
class GateEvent:
     gate: str
     status: str
     reason: str | None = None

     def as_dict(self) -> Dict[str, Any]:
         data = {"gate": self.gate, "status": self.status}
         if self.reason:
             data["reason"] = self.reason
         return data
