# PM Next Steps

Date: 2025-12-30

## Immediate (Build kickoff — B00)
1. **Open Cursor on** `C:\RichPanel_GIT` (the git clone).
2. Pull latest `main`.
3. Run the Cursor-agent prompts in `REHYDRATION_PACK/06_AGENT_ASSIGNMENTS.md` (Agent 1 → Agent 2 → Agent 3, sequentially).
4. Let each agent raise a PR and immediately run `gh pr merge --auto --merge --delete-branch` (manual merges are no longer allowed—auto-merge will land the PR once `validate` passes and delete the branch).

## Human inputs that will be needed soon
- AWS account/credentials (or confirm how AWS auth is being handled locally).
- Richpanel API access / auth method.
- Any email provider credentials for sending (if applicable).
- Final confirmation of order status mapping + SLA language used for the “delivery estimate only” messaging.

## After B00 merges
Proceed with Sprint 0/1 work in `docs/12_Cursor_Agent_Work_Packages/00_Overview/Implementation_Sequence_Sprints.md`.
