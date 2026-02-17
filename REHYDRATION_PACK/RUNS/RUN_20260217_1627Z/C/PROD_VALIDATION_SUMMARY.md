# PROD Validation Summary (Read-Only)

Source report: `REHYDRATION_PACK/RUNS/RUN_20260217_1627Z/C/live_shadow_report.json`

## Overall counts
- Total tickets evaluated: 11
- Order-status candidates: 9
- Tracking found = false with ETA available: 1
- Preorder-tagged cases detected (`preorder_proof.preorder_tag_match=true`): 3

## Non-preorder no-tracking
- Qualifying cases (tracking_found=false, preorder_delivery_estimate=false): 0
- Processing phrase present: 0
- Estimated delivery phrase present: 0
- Floor violations (`nonpreorder_floor_ok=false`): 0

## Preorder no-tracking
- Qualifying cases (tracking_found=false, preorder_delivery_estimate=true): 0
- Processing phrase present: 0
- Ship schedule phrase present: 0
- Delivery window phrase present: 0

## Notes
- Sample run used explicit ticket IDs (redacted in reports).
- No qualifying no-tracking order-status cases were present in the sampled tickets; additional prod tickets are required to fully validate no-tracking message wording and floor checks.
