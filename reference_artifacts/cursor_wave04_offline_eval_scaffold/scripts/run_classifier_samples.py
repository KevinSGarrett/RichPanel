"""Run the classifier on sample messages and print validated JSON outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from mw_llm.classifier import ClassifierClient, MockClassifierClient
from mw_llm.config import ClassifierConfig
from mw_llm.types import ClassificationFeatures, ClassificationInput


def parse_args() -> argparse.Namespace:
     parser = argparse.ArgumentParser(description="Run classifier on sample inputs.")
     parser.add_argument(
         "--samples",
         type=Path,
         default=Path("samples") / "sample_messages.jsonl",
         help="Path to JSONL file with sample messages.",
     )
     parser.add_argument("--mock-model", action="store_true", help="Use heuristic mock classifier.")
     return parser.parse_args()


def _load_samples(path: Path):
     with path.open("r", encoding="utf-8") as handle:
         for line in handle:
             if not line.strip():
                 continue
             yield json.loads(line)


def main() -> None:
     args = parse_args()
     classifier = (
         MockClassifierClient()
         if args.mock_model
         else ClassifierClient(ClassifierConfig(enable_mock_mode=False))
     )
     for sample in _load_samples(args.samples):
         features = ClassificationFeatures(
             channel=sample.get("channel", "email"),
             deterministic_order_link=sample.get("deterministic_order_link"),
             has_order_number=sample.get("has_order_number", False),
             has_email=sample.get("has_email", False),
             has_phone=sample.get("has_phone", False),
             has_tracking_number=sample.get("has_tracking_number", False),
         )
         classification_input = ClassificationInput(
             text=sample["text"],
             features=features,
         )
         decision = classifier.classify(classification_input)
         print(json.dumps({"conversation_id": sample.get("conversation_id"), "decision": decision}, indent=2))


if __name__ == "__main__":
     main()
