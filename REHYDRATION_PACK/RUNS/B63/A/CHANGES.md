# Changes — B63/A

## Code
- Added `scripts/b63_sandbox_scenarios.py` wrapper for golden path + new sandbox scenarios.
- Added shared helpers in `scripts/sandbox_scenario_utils.py` and reused in B62/B63 to avoid duplication.
- Added `--wait-seconds` passthrough for slower sandbox ticket updates.
- Removed unused follow-up scaffolding from the B63 wrapper.

## Artifacts
- `REHYDRATION_PACK/RUNS/B63/A/PROOF/sandbox_golden_path_proof.json`
- `REHYDRATION_PACK/RUNS/B63/A/PROOF/sandbox_non_order_status_proof.json`
- `REHYDRATION_PACK/RUNS/B63/A/PROOF/sandbox_order_status_no_match_proof.json`
- `REHYDRATION_PACK/RUNS/B63/A/PROOF/sandbox_order_status_order_number_proof.json`
- `REHYDRATION_PACK/RUNS/B63/A/EVIDENCE.md`
- `REHYDRATION_PACK/RUNS/B63/A/RUN_REPORT.md`

## Diffstat
```
REHYDRATION_PACK/RUNS/B63/A/CHANGES.md |   5 +-
scripts/b62_sandbox_golden_path.py     | 111 ++++---------------------------
scripts/b63_sandbox_scenarios.py       | 115 +++------------------------------
scripts/sandbox_scenario_utils.py      | 102 +++++++++++++++++++++++++++++
scripts/test_b62_golden_path.py        |   8 +--
5 files changed, 133 insertions(+), 208 deletions(-)
```
