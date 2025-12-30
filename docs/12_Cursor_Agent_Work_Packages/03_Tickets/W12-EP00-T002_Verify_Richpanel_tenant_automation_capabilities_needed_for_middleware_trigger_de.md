# W12-EP00-T002 — Verify Richpanel tenant automation capabilities needed for middleware trigger (deferred Wave 03 items)

Last updated: 2025-12-23

## Owner / Agent (suggested)
Ops (Richpanel Admin) + Backend

## Objective
Confirm the exact Richpanel UI capabilities for triggering HTTP Targets and authenticating requests so implementation matches tenant reality.

## Context / References
- `docs/03_Richpanel_Integration/Webhooks_and_Event_Handling.md`
- `docs/03_Richpanel_Integration/Automation_Rules_and_Config_Inventory.md`
- `docs/06_Security_Privacy_Compliance/Webhook_Auth_and_Request_Validation.md`
- `docs/ROADMAP.md`

## Dependencies
- W12-EP00-T001

## Implementation steps
1. In Richpanel admin, identify where HTTP Targets can be triggered from (Tagging Rules vs Assignment Rules).
1. Confirm whether HTTP Targets support custom headers (preferred auth).
1. Test whether templating of message text into JSON is safe (quotes/newlines) or whether we must send ticket_id only.
1. Record findings (YES/NO + screenshot redacting PII) and update `docs/03_Richpanel_Integration/*` if needed.

## Acceptance criteria
- [ ] A short markdown report exists under `docs/Waves/Wave_12_Cursor_Agent_Execution_Packs/` summarizing results + screenshots (PII redacted).
- [ ] A decision is recorded for webhook auth method based on tenant capability (header token vs body token).

## Test plan
- N/A (tenant verification task).

## Rollout / Release notes
- Feature flags: `safe_mode`, `automation_enabled`, per-template toggles (see Wave 06/07).

## Security / Privacy notes
- Redact any customer info in screenshots.
- Do not share API keys in screenshots.

## Deliverables
- Implementation (code/IaC/config) per ticket scope
- Tests passing (as specified)
- Cursor summary (what changed + how to run)
