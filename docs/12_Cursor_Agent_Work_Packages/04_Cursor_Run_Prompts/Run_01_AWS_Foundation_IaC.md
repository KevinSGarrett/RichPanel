# Run 01 — AWS Foundation + IaC Scaffold (EP01 + EP02)

Use this run to establish cloud foundations and repeatable deployments.

## Tickets targeted
- W12-EP01-T010
- W12-EP01-T011
- W12-EP01-T012
- W12-EP01-T013
- W12-EP02-T020

## Prompt (copy/paste)
You are a Cursor builder agent. Implement the tickets listed above exactly as specified in:
- `docs/12_Cursor_Agent_Work_Packages/03_Tickets/`

Requirements:
- Follow least-privilege IAM guidance in `docs/06_Security_Privacy_Compliance/`
- Do not commit secrets
- Produce a short run report and any IaC commands needed to deploy dev

Deliverables:
- IaC scaffold for dev environment
- Role separation (ingress vs worker)
- Secrets/SSM namespaces created
- Evidence: deploy and destroy dev stack at least once
