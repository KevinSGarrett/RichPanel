# Run 04 — LLM Routing + Policy Engine (EP06)

## Tickets targeted
- W12-EP06-T060
- W12-EP06-T061
- W12-EP06-T062
- W12-EP06-T063
- W12-EP06-T064

## Prompt (copy/paste)
Implement the LLM routing stack as advisory only, with strict schema validation and authoritative policy gates.
Hard rules:
- Tier 0 never auto-sends
- Tier 2 requires deterministic match + verifier approval
- Tier 3 disabled
- Fail-closed behavior on schema errors

Deliverables:
- Classifier + verifier wrappers
- Policy engine integration
- CI regression gates wired (golden set job stub ok if dataset not finalized)
