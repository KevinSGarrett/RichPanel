# GO-LIVE CHECKLIST (Human Only)

## Preconditions
- PR merged.
- PROD deploy already completed from B87 deploy run:
  - https://github.com/KevinSGarrett/RichPanel/actions/runs/22103028676
- Final validation report confirms:
  - floor violations = 0
  - processing phrase present where expected

## Restore PROD flags (human only)
```
aws ssm put-parameter --name /rp-mw/prod/safe_mode --type String --value false --overwrite --profile rp-admin-prod --region us-east-2
aws ssm put-parameter --name /rp-mw/prod/automation_enabled --type String --value true --overwrite --profile rp-admin-prod --region us-east-2
```

If SCP prevents this, use the approved internal method/console workflow.

## Verify flags after restore
```
aws ssm get-parameters --names /rp-mw/prod/safe_mode /rp-mw/prod/automation_enabled --with-decryption --profile rp-admin-prod --region us-east-2
```

## Optional verification
- Run `python scripts/order_status_preflight_check.py --env prod` once more.
- Monitor the first 10–20 order-status tickets in Richpanel to confirm behavior.
