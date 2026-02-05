# AWS preflight fail (wrong account expectation)

Command:
`python -c "import sys; sys.path.insert(0, 'C:\RichPanel_GIT\scripts'); from secrets_preflight import run_secrets_preflight; run_secrets_preflight(env_name='dev', region='us-east-2', profile='rp-admin-dev', expected_account_id='878145708918', require_secrets=['rp-mw/dev/richpanel/api_key'], fail_on_error=True)"`

Output (ARN redacted):
```
[AWS PREFLIGHT] account_id=151124909266 arn=[REDACTED_ARN] region=us-east-2
AWS preflight failed: wrong account (expected 878145708918, got 151124909266). Re-run with the correct AWS profile/role for the intended account (e.g., AWS_PROFILE=rp-admin-prod) in region us-east-2. (expected_env=prod, actual_env=dev)
```
