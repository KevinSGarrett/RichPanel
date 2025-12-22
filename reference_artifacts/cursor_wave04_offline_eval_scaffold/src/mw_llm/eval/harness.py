"""Offline evaluation harness skeleton."""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from ..classifier import ClassifierClient, MockClassifierClient
from ..config import ClassifierConfig, EvalConfig, Tier2VerifierConfig
from ..policy import PolicyContext, PolicyEngine
from ..tier2_verifier import Tier2VerifierClient, MockTier2VerifierClient
from .data_loader import ConversationExample, load_examples
from .metrics import EvalRecord, build_metrics, confusion_matrix, tier0_report, tier2_report

logger = logging.getLogger(__name__)

TIER0_KEYWORDS = ("chargeback", "lawsuit", "attorney", "fraud", "harassment", "threat")


class OfflineEvalHarness:
     def __init__(self, eval_config: Optional[EvalConfig] = None, use_mock_model: bool = False):
         self.eval_config = eval_config or EvalConfig()
         classifier_config = ClassifierConfig(enable_mock_mode=use_mock_model)
         verifier_config = Tier2VerifierConfig(enable_mock_mode=use_mock_model)
         self.classifier = (
             MockClassifierClient() if classifier_config.enable_mock_mode else ClassifierClient(classifier_config)
         )
         tier2_client = (
             MockTier2VerifierClient()
             if verifier_config.enable_mock_mode
             else Tier2VerifierClient(verifier_config)
         )
         self.policy = PolicyEngine(tier2_client=tier2_client)

     def run(
         self,
         sc_data_path: Path,
         labels_path: Path,
         *,
         limit: Optional[int] = None,
         output_dir: Optional[Path] = None,
     ) -> Dict[str, object]:
         output_root = output_dir or self.eval_config.ensure_output_dir()
         examples = load_examples(sc_data_path, limit=limit)
         labels = self._load_labels(labels_path)
         records: List[EvalRecord] = []

         for example in examples:
             gold_intent = labels.get(example.conversation_id)
             if not gold_intent:
                 continue
             tier0_reason = self._tier0_reason(example.raw_text)
             policy_context = PolicyContext(
                 channel=example.channel,
                 deterministic_order_link=example.features.deterministic_order_link,
                 tier0_override_reason=tier0_reason,
             )
             decision = self.classifier.classify(example.to_classification_input())
             outcome = self.policy.apply(decision, policy_context, example.redacted_text)
             records.append(
                 EvalRecord(
                     conversation_id=example.conversation_id,
                     gold_intent=gold_intent,
                     predicted_intent=outcome.decision["primary_intent"],
                     predicted_tier=outcome.decision["automation"]["tier"],
                     gate_report=outcome.gate_report,
                     tier2_attempted=outcome.tier2_attempted,
                     tier2_allowed=outcome.tier2_allowed,
                 )
             )

         metrics = build_metrics(records)
         cmatrix = confusion_matrix(records)
         tier0 = tier0_report(records)
         tier2 = tier2_report(records)

         self._write_json(output_root / self.eval_config.metrics_filename, metrics)
         self._write_json(output_root / self.eval_config.tier0_report_filename, tier0)
         self._write_json(output_root / self.eval_config.tier2_report_filename, tier2)
         self._write_confusion_matrix(output_root / self.eval_config.confusion_matrix_filename, cmatrix)

         return {
             "metrics": metrics,
             "tier0_report": tier0,
             "tier2_report": tier2,
             "confusion_matrix": cmatrix,
         }

     @staticmethod
     def _load_labels(path: Path) -> Dict[str, str]:
         labels: Dict[str, str] = {}
         with path.open("r", encoding="utf-8") as handle:
             reader = csv.DictReader(handle)
             for row in reader:
                 cid = row.get("conversation_id")
                 intent = row.get("primary_intent")
                 if cid and intent:
                     labels[cid] = intent.strip()
         return labels

     @staticmethod
     def _write_json(path: Path, payload: Dict[str, object]) -> None:
         with path.open("w", encoding="utf-8") as handle:
             json.dump(payload, handle, indent=2)

     @staticmethod
     def _write_confusion_matrix(path: Path, matrix: Dict[str, Dict[str, int]]) -> None:
         intents = sorted({*matrix.keys(), *(pred for row in matrix.values() for pred in row.keys())})
         with path.open("w", newline="", encoding="utf-8") as handle:
             writer = csv.writer(handle)
             writer.writerow(["gold \\ predicted", *intents])
             for gold_intent in intents:
                 row = [gold_intent]
                 for pred_intent in intents:
                     row.append(matrix.get(gold_intent, {}).get(pred_intent, 0))
                 writer.writerow(row)

     @staticmethod
     def _tier0_reason(text: str | None) -> Optional[str]:
         if not text:
             return None
         lowered = text.lower()
         for keyword in TIER0_KEYWORDS:
             if keyword in lowered:
                 return f"keyword:{keyword}"
         return None
