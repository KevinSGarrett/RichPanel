# Go-Live Checklist (Human-Only)

**Run ID:** `RUN_20260216_0343Z`  
**Date (UTC):** 2026-02-16  
**Environment:** prod (us-east-2)

## Current confirmed PROD flags
- safe_mode=true
- automation_enabled=false

## Human go-live steps (do NOT execute here)
1) Enable automation (optional staged):
```
aws ssm put-parameter --name "/rp-mw/prod/automation_enabled" --value "true" --type "String" --overwrite --region us-east-2
```
2) Allow outbound replies:
```
aws ssm put-parameter --name "/rp-mw/prod/safe_mode" --value "false" --type "String" --overwrite --region us-east-2
```

## Monitoring checklist
- CloudWatch logs for middleware Lambda (errors, warnings, throughput).
- Error rates and throttling (5xx, retry spikes).
- Richpanel API 429 / Retry-After behavior.

## Rollback plan
- Immediately set safe_mode=true and automation_enabled=false if anomalies observed:
```
aws ssm put-parameter --name "/rp-mw/prod/safe_mode" --value "true" --type "String" --overwrite --region us-east-2
aws ssm put-parameter --name "/rp-mw/prod/automation_enabled" --value "false" --type "String" --overwrite --region us-east-2
```

