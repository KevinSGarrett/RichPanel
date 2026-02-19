Redaction notes

- `prod_worker_lambda_config_redacted.json` redacts secret values, ARNs, account IDs, and SSM parameter paths using `***REDACTED***`.
- `prod_shadow_report.json` redacts `api_key_secret_id` and `api_key_hash`.
- `shadow_eval_run_22162429932.log` redacts the Shopify domain and ticket IDs.
- `prod_flags_snapshot.json` redacts SSM parameter ARNs.
- `deploy_prod_log.txt` redacts AWS account IDs in log output.
- `sts_identity_prod.json` redacts account/ARN/user identifiers.
- `OPENAI_REPLY_REWRITE_MODEL` and `OPENAI_REPLY_REWRITE_TEMPERATURE` are intentionally left visible because they are non-sensitive configuration values required as proof.
