# Changes — B62/A

## Intent
- Add B62 sandbox golden path wrapper and proof-field strengthening.
- Add unit tests for outbound classification and reply content flags.

## Diffstat
```
scripts/create_sandbox_email_ticket.py                 |  16 +++
scripts/dev_e2e_smoke.py                               | 203 +++++++++++++++++++++++++++++++--
scripts/test_e2e_smoke_encoding.py                     | 114 ++++++++++++++++++
scripts/b62_sandbox_golden_path.py                     | 487 ++++++++++++++++++++++++++++++
scripts/sandbox_golden_path_proof.py                   |  14 ++++++++++++++
scripts/test_b62_golden_path.py                        |  64 ++++++++++++++++++++++++++++++++++
REHYDRATION_PACK/RUNS/B62/A/RUN_REPORT.md              |   8 ++++++++
REHYDRATION_PACK/RUNS/B62/A/EVIDENCE.md                |  80 +++++++++++++++++++++++++++++
REHYDRATION_PACK/RUNS/B62/A/CHANGES.md                 |  20 ++++++++++++++++++++
REHYDRATION_PACK/RUNS/B62/A/PROOF/created_ticket.json  |  27 ++++++++++++++++++++++
REHYDRATION_PACK/RUNS/B62/A/PROOF/golden_path.json     | 502 +++++++++++++++++++++
REHYDRATION_PACK/RUNS/B62/A/PROOF/sandbox_golden_path_proof.json | 502 +++++++++++++++++++++
```
