## Prod Shadow Run Attempts (B69)

### Attempt 1: deterministic (skip OpenAI intent)
Command:
```
python scripts/prod_shadow_order_status_report.py --env prod --sample-size 200 --allow-ticket-fetch-failures --skip-openai-intent --out-json REHYDRATION_PACK/RUNS/B69/C/PROOF/prod_shadow_report_200_deterministic.json --out-md REHYDRATION_PACK/RUNS/B69/C/PROOF/prod_shadow_report_200_deterministic.md
```

Result:
- Failed to load Richpanel API key from AWS Secrets Manager.
- Error: `botocore.exceptions.NoCredentialsError: Unable to locate credentials`

### Notes
- AWS region was set to `us-east-1` and required read-only env flags were enabled.
- Run requires valid AWS credentials to fetch Richpanel secrets.

### Attempt 2: prod profile (placeholder API key)
Command:
```
AWS_PROFILE=rp-admin-prod ... python scripts/prod_shadow_order_status_report.py --env prod --sample-size 200 --allow-ticket-fetch-failures --skip-openai-intent --out-json REHYDRATION_PACK/RUNS/B69/C/PROOF/prod_shadow_report_200_deterministic.json --out-md REHYDRATION_PACK/RUNS/B69/C/PROOF/prod_shadow_report_200_deterministic.md
```

Result:
- Ticket listing failed with HTTP 403.
- Secrets Manager shows `rp-mw/prod/richpanel/api_key` is a placeholder description, so the API key appears invalid.

### Attempt 3: API key override (listing 403)
Command:
```
RICHPANEL_API_KEY_OVERRIDE=<set> python scripts/prod_shadow_order_status_report.py --env prod --sample-size 200 --allow-ticket-fetch-failures --skip-openai-intent ...
```

Result:
- Ticket listing failed with HTTP 403 on `GET /v1/tickets` (fallbacks to `/api/v1/conversations` and `/v1/conversations` also 403).
- Direct ticket fetch works (verified separately), so listing permissions appear restricted.
