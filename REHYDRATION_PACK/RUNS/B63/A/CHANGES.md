# Changes — B63/A

## Code
- Added `scripts/b63_sandbox_scenarios.py` wrapper for golden path + new sandbox scenarios.
- Added shared helpers in `scripts/sandbox_scenario_utils.py` and reused in B62/B63, dev smoke, and sandbox ticket scripts to avoid duplication.
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
REHYDRATION_PACK/RUNS/B63/A/CHANGES.md             |  25 +
REHYDRATION_PACK/RUNS/B63/A/EVIDENCE.md            |  51 ++
REHYDRATION_PACK/RUNS/B63/A/PROOF/created_ticket_golden_path.json    |  27 +
REHYDRATION_PACK/RUNS/B63/A/PROOF/created_ticket_non_order_status.json   |  27 +
REHYDRATION_PACK/RUNS/B63/A/PROOF/created_ticket_order_status_no_match.json      |  27 +
REHYDRATION_PACK/RUNS/B63/A/PROOF/created_ticket_order_status_order_number.json  |  27 +
REHYDRATION_PACK/RUNS/B63/A/PROOF/sandbox_golden_path_proof.json     | 501 +++++++++++++
REHYDRATION_PACK/RUNS/B63/A/PROOF/sandbox_non_order_status_proof.json    | 403 +++++++++++
REHYDRATION_PACK/RUNS/B63/A/PROOF/sandbox_order_status_no_match_proof.json | 469 ++++++++++++
REHYDRATION_PACK/RUNS/B63/A/PROOF/sandbox_order_status_order_number_proof.json   | 478 ++++++++++++
REHYDRATION_PACK/RUNS/B63/A/RUN_REPORT.md          |  23 +
scripts/b62_sandbox_golden_path.py                 | 111 +--
scripts/b63_sandbox_scenarios.py                   | 802 +++++++++++++++++++++
scripts/sandbox_scenario_utils.py                  | 102 +++
scripts/test_b62_golden_path.py                    |   8 +-
15 files changed, 2980 insertions(+), 101 deletions(-)
```
