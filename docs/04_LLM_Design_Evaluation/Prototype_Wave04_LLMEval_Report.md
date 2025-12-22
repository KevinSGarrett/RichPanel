## Wave 04 — LLM Routing & Offline Eval Scaffold

### What was built
- Strict runtime validation for `mw_decision_v1` and `mw_tier2_verifier_v1` schemas with negative/positive tests (`mw_llm.schema_validation` + `tests/test_schema_validation.py`).
- OpenAI Responses API wrappers (`mw_llm.classifier.ClassifierClient`, `mw_llm.tier2_verifier.Tier2VerifierClient`) that auto-load the prompt markdown, request structured outputs, validate responses, and fail closed with a deterministic fallback.
- Application-layer policy engine (`mw_llm.policy.PolicyEngine`) that enforces Tier 0 overrides, Tier 2 deterministic-match requirements + verifier approvals, and Tier 3 disablement. Tests cover every gate.
- Redaction helpers (`mw_llm.redaction`) and tests that scrub emails, phones, order numbers, and tracking IDs before logs/eval.
- Offline evaluation harness (`mw_llm.eval.harness` + `scripts/run_eval.py`) that loads the SC_Data AI-ready package, applies the classifier + policy gates, and emits accuracy, macro F1, per-intent precision/recall, confusion matrix, Tier 0 FN/FP report, and Tier 2 eligibility counts.
- Utility scripts and sample data (`samples/sample_messages.jsonl`, `data/sample_labels.csv`) plus `scripts/run_classifier_samples.py` for quick local smoke tests.

### How to run locally
1. **Install deps**
   ```bash
   pip install -e .
   ```
2. **Env vars**
   - `OPENAI_API_KEY` for live calls.
   - Optional overrides: `MW_CLASSIFIER_MODEL`, `MW_TIER2_MODEL`, `MW_LLM_OFFLINE_MODE=1` to force mock mode.
3. **Classifier smoke test**
   ```bash
   PYTHONPATH=src python scripts/run_classifier_samples.py --mock-model
   ```
   Remove `--mock-model` to hit OpenAI; outputs validated JSON per sample input.
4. **Offline eval**
   ```bash
   PYTHONPATH=src python scripts/run_eval.py \
       --sc-data c:\path\to\SC_Data_ai_ready_package.zip \
       --labels data\sample_labels.csv \
       --mock-model \
       --output-dir artifacts
   ```
   Artifacts land under `artifacts/` (`metrics.json`, `confusion_matrix.csv`, `tier0_report.json`, `tier2_report.json`).

### Example metrics (mock model, 5-sample label file)
```artifacts/metrics.json
{
  "accuracy": 0.6,
  "macro_f1": 0.444,
  "per_intent": {
    "order_status_tracking": {"precision": 0.0, "recall": 0.0, "f1": 0.0, "support": 1},
    "cancel_subscription": {"precision": 1.0, "recall": 1.0, "f1": 1.0, "support": 1},
    "damaged_item": {"precision": 1.0, "recall": 1.0, "f1": 1.0, "support": 1},
    "technical_support": {"precision": 0.0, "recall": 0.0, "f1": 0.0, "support": 1},
    "fraud_suspected": {"precision": 1.0, "recall": 1.0, "f1": 1.0, "support": 1}
  }
}
```
Tier 0 report (`artifacts/tier0_report.json`) shows no FN/FP on the sample, and Tier 2 eligibility report confirms 0 violations because the policy engine downgrades every non-compliant recommendation before any verifier attempt.

### Policy gate assurances
- `tests/test_policy.py` covers Tier 0 overrides, Tier 2 deterministic-match downgrades, Tier 2 verifier denials, and Tier 3 disablement. Even if the model suggests unsafe automation, `PolicyEngine.apply` forces escalation or Tier 1 + route-only paths and logs structured gate reports for observability.
- `mw_llm.classifier` fallback always tags `mw-model-failure`, sets `needs_manual_triage`, and avoids automation.

### Redaction & logging
- `mw_llm.redaction.redact_text` powers the data loader so evaluation artifacts never contain raw emails, phones, or order/tracking numbers.
- Unit tests in `tests/test_redaction.py` verify detection heuristics.

This scaffold is non-production by design but wires every Wave 04 artifact (prompts, schemas, policy) into runnable Python so we can calibrate thresholds and expand datasets iteratively.
