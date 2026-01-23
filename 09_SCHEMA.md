# Claude Gap-Filler Output Schema (v1)

Claude must output **valid JSON** matching this shape:

```json
{
  "version": "1.0",
  "verdict": "PASS",
  "risk": "risk:R2",
  "reviewers": [
    {
      "name": "primary",
      "model": "claude-opus-4-5-20251101",
      "findings": [
        {
          "finding_id": "a1b2c3d4e5f6",
          "category": "correctness|security|reliability|infra|tests|observability",
          "severity": 0,
          "confidence": 0,
          "title": "Short title",
          "summary": "One sentence summary",
          "file": "path/to/file.py",
          "evidence": "short quote from diff",
          "suggested_fix": "optional short suggestion",
          "suggested_test": "optional test idea"
        }
      ]
    }
  ]
}
```

Rules:
- `severity` integer 0–5
- `confidence` integer 0–100
- `finding_id` must be stable and deterministic per reviewer (best-effort).
- For severity >= 3:
  - `file` must be non-empty
  - `evidence` must be non-empty and match diff text
  - `confidence` should usually be >= 70
- If no findings, return an empty array for `findings`.

The script will compute:
- agreement counts across reviewers (same `finding_id`)
- point totals and Action Required list
