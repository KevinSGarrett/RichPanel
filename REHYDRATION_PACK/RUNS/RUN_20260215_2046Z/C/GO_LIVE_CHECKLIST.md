# Go-Live Checklist (Human-only)

**Run ID:** `RUN_20260215_2046Z`  
**Date (UTC):** 2026-02-15  
**Scope:** PROD automation toggle checklist (read-only evidence run; no execution here)

## Current PROD state (observed)
- `/rp-mw/prod/safe_mode` = `true` (Version 3, LastModifiedDate 2026-02-13T21:29:00.267000-06:00)
- `/rp-mw/prod/automation_enabled` = `false` (Version 4, LastModifiedDate 2026-02-13T21:30:57.825000-06:00)

## WARNING
Changing these flags can cause customer contact. Only a human operator should execute the commands below after confirming timing, approvals, and rollback plan.

## Pre-flight (record current values)
1) Capture current versions/timestamps for rollback:
   - `aws ssm get-parameters --names "/rp-mw/prod/safe_mode" "/rp-mw/prod/automation_enabled" --region us-east-2`

## Staged rollout (recommended)
1) **Optional shadow/plan-only phase** (no replies):
   - Keep `safe_mode=true`, set `automation_enabled=true`.
   - Command:
     - `aws ssm put-parameter --name "/rp-mw/prod/automation_enabled" --type String --value "true" --overwrite --region us-east-2`
2) **Go-live (replies enabled)**:
   - Set `safe_mode=false` while `automation_enabled=true`.
   - Commands:
     - `aws ssm put-parameter --name "/rp-mw/prod/safe_mode" --type String --value "false" --overwrite --region us-east-2`
     - `aws ssm put-parameter --name "/rp-mw/prod/automation_enabled" --type String --value "true" --overwrite --region us-east-2`

## Rollback (immediate)
- Revert to no-contact state:
  - `aws ssm put-parameter --name "/rp-mw/prod/safe_mode" --type String --value "true" --overwrite --region us-east-2`
  - `aws ssm put-parameter --name "/rp-mw/prod/automation_enabled" --type String --value "false" --overwrite --region us-east-2`

## Post-change validation (human)
- Re-read parameters to confirm values:
  - `aws ssm get-parameters --names "/rp-mw/prod/safe_mode" "/rp-mw/prod/automation_enabled" --region us-east-2`
