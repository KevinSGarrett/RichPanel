# Command log (B71/A)

```
python scripts\secrets_preflight.py --env dev --region us-east-2 --expect-account-id 151124909266 --require-secret rp-mw/dev/richpanel/api_key
python scripts\secrets_preflight.py --env dev --profile rp-admin-dev --region us-east-2 --expect-account-id 151124909266 --require-secret rp-mw/dev/richpanel/api_key
aws --version
aws sso login --profile rp-admin-dev
python scripts\secrets_preflight.py --env dev --profile rp-admin-dev --region us-east-2 --expect-account-id 151124909266 --require-secret rp-mw/dev/richpanel/api_key
python scripts\secrets_preflight.py --env dev --profile rp-admin-dev --region us-east-2 --expect-account-id 878145708918 --require-secret rp-mw/dev/richpanel/api_key
python -c "from secrets_preflight import run_secrets_preflight; run_secrets_preflight(env_name='dev', region='us-east-2', profile='rp-admin-dev', expected_account_id='878145708918', require_secrets=['rp-mw/dev/richpanel/api_key'], fail_on_error=True)"
python -c "import sys; sys.path.insert(0, 'C:\\RichPanel_GIT\\scripts'); from secrets_preflight import run_secrets_preflight; run_secrets_preflight(env_name='dev', region='us-east-2', profile='rp-admin-dev', expected_account_id='878145708918', require_secrets=['rp-mw/dev/richpanel/api_key'], fail_on_error=True)"
python scripts\test_shopify_client.py
python scripts\test_live_readonly_shadow_eval.py
python scripts\test_shadow_order_status.py
python scripts\regen_doc_registry.py
python scripts\regen_reference_registry.py
python scripts\regen_plan_checklist.py
python scripts\test_secrets_preflight.py
python scripts\test_shopify_health_check.py
python scripts\test_shopify_client.py
python scripts\test_live_readonly_shadow_eval.py
python scripts\test_shadow_order_status.py
python scripts\test_shopify_client.py
```
