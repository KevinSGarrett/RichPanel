"""Offline evaluation metrics helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

from ..policy import TIER0_INTENTS, TIER2_ALLOWLIST


@dataclass(slots=True)
class EvalRecord:
     conversation_id: str
     gold_intent: str
     predicted_intent: str
     predicted_tier: str
     gate_report: List[Dict[str, str]]
     tier2_attempted: bool
     tier2_allowed: bool

     @property
     def tier0_gold(self) -> bool:
         return self.gold_intent in TIER0_INTENTS

     @property
     def tier0_pred(self) -> bool:
         return self.predicted_tier == "TIER_0_ESCALATION"


def _per_intent_counts(records: Iterable[EvalRecord]) -> Dict[str, Dict[str, int]]:
     intents: Dict[str, Dict[str, int]] = {}
     for record in records:
         intents.setdefault(record.gold_intent, {"tp": 0, "fp": 0, "fn": 0})
         intents.setdefault(record.predicted_intent, {"tp": 0, "fp": 0, "fn": 0})
         if record.gold_intent == record.predicted_intent:
             intents[record.gold_intent]["tp"] += 1
         else:
             intents[record.gold_intent]["fn"] += 1
             intents[record.predicted_intent]["fp"] += 1
     return intents


def _precision_recall_f1(counts: Dict[str, int]) -> Tuple[float, float, float]:
     tp = counts.get("tp", 0)
     fp = counts.get("fp", 0)
     fn = counts.get("fn", 0)
     precision = tp / (tp + fp) if (tp + fp) else 0.0
     recall = tp / (tp + fn) if (tp + fn) else 0.0
     if precision + recall == 0:
         f1 = 0.0
     else:
         f1 = 2 * precision * recall / (precision + recall)
     return precision, recall, f1


def build_metrics(records: List[EvalRecord]) -> Dict[str, object]:
     total = len(records)
     if total == 0:
         return {
             "accuracy": 0.0,
             "macro_f1": 0.0,
             "per_intent": {},
         }
     accuracy = sum(1 for record in records if record.gold_intent == record.predicted_intent) / total
     per_intent_counts = _per_intent_counts(records)
     per_intent_metrics: Dict[str, Dict[str, float]] = {}
     macro_f1_sum = 0.0
     for intent, counts in per_intent_counts.items():
         precision, recall, f1 = _precision_recall_f1(counts)
         per_intent_metrics[intent] = {
             "precision": precision,
             "recall": recall,
             "f1": f1,
             "support": counts.get("tp", 0) + counts.get("fn", 0),
         }
         macro_f1_sum += f1
     macro_f1 = macro_f1_sum / len(per_intent_counts)
     return {
         "accuracy": accuracy,
         "macro_f1": macro_f1,
         "per_intent": per_intent_metrics,
     }


def confusion_matrix(records: List[EvalRecord]) -> Dict[str, Dict[str, int]]:
     matrix: Dict[str, Dict[str, int]] = {}
     for record in records:
         matrix.setdefault(record.gold_intent, {})
         matrix[record.gold_intent].setdefault(record.predicted_intent, 0)
         matrix[record.gold_intent][record.predicted_intent] += 1
     return matrix


def tier0_report(records: List[EvalRecord]) -> Dict[str, object]:
     false_negatives = [
         record.conversation_id for record in records if record.tier0_gold and not record.tier0_pred
     ]
     false_positives = [
         record.conversation_id for record in records if not record.tier0_gold and record.tier0_pred
     ]
     return {
         "fn": false_negatives,
         "fp": false_positives,
         "fn_rate": len(false_negatives),
         "fp_rate": len(false_positives),
     }


def tier2_report(records: List[EvalRecord]) -> Dict[str, object]:
     attempted = sum(1 for record in records if record.tier2_attempted)
     allowed = sum(1 for record in records if record.tier2_allowed)
     denied = attempted - allowed
     violations = sum(
         1
         for record in records
         if record.predicted_tier == "TIER_2_VERIFIED" and record.predicted_intent not in TIER2_ALLOWLIST
     )
     return {
         "attempted": attempted,
         "allowed": allowed,
         "denied": denied,
         "violations": violations,
     }
