# Current Cursor Agent Prompts (build mode)

## Prompt — Agent A (not assigned in this cycle)
```text
RUN_ID: RUN_20260103_2300Z
Agent: A

No tasks assigned in this cycle. Do not make changes.
```

## Prompt — Agent B (not assigned in this cycle)
```text
RUN_ID: RUN_20260103_2300Z
Agent: B

No tasks assigned in this cycle. Do not make changes.
```

## Prompt — Agent C (Evidence/runbook alignment + prompt hygiene; no drift)
```text
RUN_ID: RUN_20260103_2300Z
Agent: C

Objective
- Keep us aligned and prevent prompt drift:
  - Ensure REHYDRATION_PACK/06_AGENT_ASSIGNMENTS.md contains ONLY current prompts (archive elsewhere)
  - Ensure admin docs are updated and scripts/verify_admin_logs_sync.py passes
  - Ensure runbooks clearly describe how to run Dev/Staging smoke and capture evidence
  - Optional: fix any doc-hygiene warnings that are safe to fix (for example replace unicode ellipsis characters)

Idempotency check (pre-step)
- If CI is already green and admin logs are current, do not create a no-op PR. Only act if drift is detected.

Scope (allowed)
- REHYDRATION_PACK/*
- docs/00_Project_Admin/*
- docs/08_Engineering/*
- docs/10_Operations_Runbooks_Training/runbooks/*
- scripts/* (only if required for the above)

Do not touch (locked)
- backend/src/**
- infra/cdk/**

Required validations
- python scripts/verify_admin_logs_sync.py
- python scripts/run_ci_checks.py

Deliverables
- Any needed doc updates committed
- Archived prior prompts if you rewrote REHYDRATION_PACK/06_AGENT_ASSIGNMENTS.md
```
