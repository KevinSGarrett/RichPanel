"""Configuration objects for LLM clients and evaluation harness."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import os


REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(slots=True)
class ClassifierConfig:
    """Runtime configuration for the classifier call wrapper."""

    model_name: str = os.environ.get("MW_CLASSIFIER_MODEL", "gpt-5-mini")
    prompt_version: str = "classification_routing_v1"
    schema_name: str = "mw_decision_v1"
    max_retries: int = 1
    timeout_seconds: float = 30.0
    enable_mock_mode: bool = bool(os.environ.get("MW_LLM_OFFLINE_MODE"))

    @property
    def prompt_path(self) -> Path:
        return (
            REPO_ROOT
            / "docs"
            / "04_LLM_Design_Evaluation"
            / "prompts"
            / f"{self.prompt_version}.md"
        )


@dataclass(slots=True)
class Tier2VerifierConfig:
    """Runtime configuration for the Tier 2 verifier wrapper."""

    model_name: str = os.environ.get("MW_TIER2_MODEL", "gpt-4o-mini")
    prompt_version: str = "tier2_verifier_v1"
    schema_name: str = "mw_tier2_verifier_v1"
    timeout_seconds: float = 15.0
    max_retries: int = 1
    enable_mock_mode: bool = bool(os.environ.get("MW_LLM_OFFLINE_MODE"))

    @property
    def prompt_path(self) -> Path:
        return (
            REPO_ROOT
            / "docs"
            / "04_LLM_Design_Evaluation"
            / "prompts"
            / f"{self.prompt_version}.md"
        )


@dataclass(slots=True)
class EvalConfig:
    """Configuration helper for the offline evaluation harness."""

    output_dir: Path = REPO_ROOT / "artifacts"
    confusion_matrix_filename: str = "confusion_matrix.csv"
    metrics_filename: str = "metrics.json"
    tier0_report_filename: str = "tier0_report.json"
    tier2_report_filename: str = "tier2_report.json"

    def ensure_output_dir(self) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        return self.output_dir
