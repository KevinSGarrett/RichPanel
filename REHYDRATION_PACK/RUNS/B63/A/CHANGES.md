# Changes — B63/A

## Code
- Added `scripts/b63_sandbox_scenarios.py` wrapper for golden path + new sandbox scenarios.
- Added `--wait-seconds` passthrough and follow-up message control for the wrapper.
- Appended per-scenario assertion blocks in proof JSON (PII-safe).

## Artifacts
- `REHYDRATION_PACK/RUNS/B63/A/PROOF/sandbox_golden_path_proof.json`
- `REHYDRATION_PACK/RUNS/B63/A/PROOF/sandbox_non_order_status_proof.json`
- `REHYDRATION_PACK/RUNS/B63/A/PROOF/sandbox_order_status_no_match_proof.json`
- `REHYDRATION_PACK/RUNS/B63/A/PROOF/sandbox_order_status_order_number_proof.json`
- `REHYDRATION_PACK/RUNS/B63/A/EVIDENCE.md`
- `REHYDRATION_PACK/RUNS/B63/A/RUN_REPORT.md`

## Diffstat
```
REHYDRATION_PACK/RUNS/B63/A/CHANGES.md             |  19 +
REHYDRATION_PACK/RUNS/B63/A/EVIDENCE.md            |  51 ++
REHYDRATION_PACK/RUNS/B63/A/PROOF/created_ticket_golden_path.json    |  27 +
REHYDRATION_PACK/RUNS/B63/A/PROOF/created_ticket_non_order_status.json   |  27 +
REHYDRATION_PACK/RUNS/B63/A/PROOF/created_ticket_order_status_no_match.json      |  27 +
REHYDRATION_PACK/RUNS/B63/A/PROOF/created_ticket_order_status_order_number.json  |  27 +
REHYDRATION_PACK/RUNS/B63/A/PROOF/sandbox_golden_path_proof.json     | 501 ++++++++++++
REHYDRATION_PACK/RUNS/B63/A/PROOF/sandbox_non_order_status_proof.json    | 403 +++++++++
REHYDRATION_PACK/RUNS/B63/A/PROOF/sandbox_order_status_no_match_proof.json | 469 +++++++++++
REHYDRATION_PACK/RUNS/B63/A/PROOF/sandbox_order_status_order_number_proof.json   | 478 +++++++++++
REHYDRATION_PACK/RUNS/B63/A/RUN_REPORT.md          |  23 +
scripts/b63_sandbox_scenarios.py                   | 897 +++++++++++++++++++++
12 files changed, 2949 insertions(+)
```
