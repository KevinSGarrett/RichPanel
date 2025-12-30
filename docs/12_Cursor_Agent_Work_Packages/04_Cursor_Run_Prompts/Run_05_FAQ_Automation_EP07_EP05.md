# Run 05 — Templates + FAQ Automation + Order Status (EP07 + EP05)

## Tickets targeted
- W12-EP07-T070
- W12-EP07-T071
- W12-EP07-T072
- W12-EP07-T073
- W12-EP05-T050
- W12-EP05-T051
- (Optional) W12-EP05-T052

## Prompt (copy/paste)
Implement template rendering and automation sending using approved templates only.
Rules:
- Model outputs template_id only; never writes customer text.
- No deterministic match → no order-specific disclosure.
- Safe_mode disables all sends.

Deliverables:
- Template renderer + unit tests
- Order linkage + variable mapping
- Tier 1 safe-assist replies + dedup
- Tier 2 order status reply with verifier gate
