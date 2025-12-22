"""Tier 2 verifier wrapper."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from openai import OpenAI

from .config import Tier2VerifierConfig
from .prompt_loader import load_prompt_sections
from .schema_validation import (
     SchemaValidationError,
     get_schema_dict,
     validate_tier2_schema,
)
from .types import Tier2VerifierInput

logger = logging.getLogger(__name__)


class Tier2VerifierClient:
     def __init__(self, config: Optional[Tier2VerifierConfig] = None, *, client: Optional[OpenAI] = None):
         self.config = config or Tier2VerifierConfig()
         self.schema_dict = get_schema_dict(self.config.schema_name)
         self.prompt_sections = load_prompt_sections(self.config.prompt_path)
         self.client = client if not self.config.enable_mock_mode else None
         if self.client is None and not self.config.enable_mock_mode:
             self.client = OpenAI()

     def verify(self, verifier_input: Tier2VerifierInput) -> Dict[str, Any]:
         if self.config.enable_mock_mode:
             return MockTier2VerifierClient().verify(verifier_input)

         attempt = 0
         last_error: Optional[Exception] = None
         while attempt <= self.config.max_retries:
             attempt += 1
             try:
                 response = self.client.responses.create(
                     model=self.config.model_name,
                     input=[
                         {"role": "system", "content": self.prompt_sections.system},
                         {"role": "user", "content": verifier_input.to_prompt()},
                     ],
                     response_format={
                         "type": "json_schema",
                         "json_schema": {"name": self.config.schema_name, "schema": self.schema_dict},
                     },
                     timeout=self.config.timeout_seconds,
                 )
                 content = response.output[0].content[0].text  # type: ignore[index]
                 parsed = json.loads(content)
                 return validate_tier2_schema(parsed)
             except (json.JSONDecodeError, SchemaValidationError) as exc:
                 last_error = exc
             except Exception as exc:  # pragma: no cover
                 last_error = exc
             if attempt <= self.config.max_retries:
                 continue
         logger.error("Tier2 verifier fallback due to error: %s", last_error)
         fallback = {
             "schema_version": "mw_tier2_verifier_v1",
             "allow_tier2": False,
             "confidence": 0.0,
             "downgrade_to_tier": "TIER_1_SAFE_ASSIST",
             "reason_code": "TOO_AMBIGUOUS",
             "notes": "Verifier failure fallback",
         }
         return validate_tier2_schema(fallback)


class MockTier2VerifierClient:
     def verify(self, verifier_input: Tier2VerifierInput) -> Dict[str, Any]:
         text = verifier_input.customer_message.lower()
         allow = (
             verifier_input.deterministic_order_link
             and verifier_input.proposed_primary_intent in {"order_status_tracking", "shipping_delay_not_shipped"}
             and not any(word in text for word in ["cancel", "refund", "chargeback", "legal"])
         )
         result = {
             "schema_version": "mw_tier2_verifier_v1",
             "allow_tier2": bool(allow),
             "confidence": 0.8 if allow else 0.2,
             "downgrade_to_tier": "TIER_1_SAFE_ASSIST" if not allow else "TIER_1_SAFE_ASSIST",
             "reason_code": "OK" if allow else "CONFLICTING_INTENT",
             "notes": "Mock verifier decision",
         }
         return validate_tier2_schema(result)
