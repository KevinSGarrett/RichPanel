"""CLI entrypoint for the offline evaluation harness."""

from __future__ import annotations

import argparse
from pathlib import Path

from mw_llm.config import EvalConfig
from mw_llm.eval.harness import OfflineEvalHarness


def parse_args() -> argparse.Namespace:
     parser = argparse.ArgumentParser(description="Run the Wave 04 offline eval harness.")
     parser.add_argument(
         "--sc-data",
         required=True,
         type=Path,
         help="Path to SC_Data_ai_ready_package.zip (or extracted folder).",
     )
     parser.add_argument(
         "--labels",
         required=True,
         type=Path,
         help="CSV with columns [conversation_id, primary_intent].",
     )
     parser.add_argument(
         "--limit",
         type=int,
         default=None,
         help="Optional limit on number of conversations to evaluate.",
     )
     parser.add_argument(
         "--output-dir",
         type=Path,
         default=None,
         help="Directory to store metrics artifacts.",
     )
     parser.add_argument(
         "--mock-model",
         action="store_true",
         help="Use heuristic mock model/tier2 verifier instead of calling OpenAI.",
     )
     return parser.parse_args()


def main() -> None:
     args = parse_args()
     harness = OfflineEvalHarness(EvalConfig(), use_mock_model=args.mock_model)
     results = harness.run(
         args.sc_data,
         args.labels,
         limit=args.limit,
         output_dir=args.output_dir,
     )
     print("Accuracy:", round(results["metrics"]["accuracy"], 3))
     print("Macro F1:", round(results["metrics"]["macro_f1"], 3))
     print("Tier 0 FN:", results["tier0_report"]["fn"])
     print("Tier 0 FP:", results["tier0_report"]["fp"])
     print("Tier 2 summary:", results["tier2_report"])


if __name__ == "__main__":
     main()
