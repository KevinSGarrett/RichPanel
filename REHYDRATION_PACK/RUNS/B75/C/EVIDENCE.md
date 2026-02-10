# B75/C Evidence (PII-safe)

## AWS prod identity
Command: aws sso login --profile rp-admin-prod
Attempting to open your default browser.
If the browser does not open, open the following URL:

https://oidc.us-east-1.amazonaws.com/authorize?response_type=code&client_id=9YC5OGMirGaE9d9UAW4YrHVzLWVhc3QtMQ&redirect_uri=http%3A%2F%2F127.0.0.1%3A56815%2Foauth%2Fcallback&state=5e9148ca-5fec-4fe6-9259-c7d8f7412a12&code_challenge_method=S256&scopes=sso%3Aaccount%3Aaccess&code_challenge=8afMR_5XZCXWjA7T2zw6QryHBi0g-5gGfCsagFYilks
Successfully logged into Start URL: https://d-9066183f41.awsapps.com/start

Command: aws sts get-caller-identity --profile rp-admin-prod --output json
{
    "UserId": "AROA4Y5MQEN3E5KRSFG44:rp-deployer-prod",
    "Account": "878145708918",
    "Arn": "arn:aws:<redacted>"
}

## Prod worker env vars (read-only proof)
Command: aws lambda get-function-configuration --function-name rp-mw-prod-worker --region us-east-2 --profile rp-admin-prod --query 'Environment.Variables.{RICHPANEL_READ_ONLY:RICHPANEL_READ_ONLY,RICHPANEL_WRITE_DISABLED:RICHPANEL_WRITE_DISABLED,RICHPANEL_OUTBOUND_ENABLED:RICHPANEL_OUTBOUND_ENABLED}' --output json
{
    "RICHPANEL_READ_ONLY": null,
    "RICHPANEL_WRITE_DISABLED": null,
    "RICHPANEL_OUTBOUND_ENABLED": null
}

## Prod SSM runtime flags (read-only proof)
Command: aws ssm get-parameters --names /rp-mw/prod/safe_mode /rp-mw/prod/automation_enabled --region us-east-2 --profile rp-admin-prod --query 'Parameters[*].[Name,Value]' --output table
---------------------------------------------
|               GetParameters               |
+----------------------------------+--------+
|  /rp-mw/prod/automation_enabled  |  false |
|  /rp-mw/prod/safe_mode           |  true  |
+----------------------------------+--------+

## Prod worker env context (PII-safe)
Command: aws lambda get-function-configuration --function-name rp-mw-prod-worker --region us-east-2 --profile rp-admin-prod --query 'Environment.Variables.{MW_ENV:MW_ENV,SAFE_MODE_PARAM:SAFE_MODE_PARAM,AUTOMATION_ENABLED_PARAM:AUTOMATION_ENABLED_PARAM,RICHPANEL_READ_ONLY:RICHPANEL_READ_ONLY,RICHPANEL_WRITE_DISABLED:RICHPANEL_WRITE_DISABLED,RICHPANEL_OUTBOUND_ENABLED:RICHPANEL_OUTBOUND_ENABLED,MW_ALLOW_ENV_FLAG_OVERRIDE:MW_ALLOW_ENV_FLAG_OVERRIDE,MW_SAFE_MODE_OVERRIDE:MW_SAFE_MODE_OVERRIDE,MW_AUTOMATION_ENABLED_OVERRIDE:MW_AUTOMATION_ENABLED_OVERRIDE}' --output json
{
    "MW_ENV": "prod",
    "SAFE_MODE_PARAM": "/rp-mw/prod/safe_mode",
    "AUTOMATION_ENABLED_PARAM": "/rp-mw/prod/automation_enabled",
    "RICHPANEL_READ_ONLY": null,
    "RICHPANEL_WRITE_DISABLED": null,
    "RICHPANEL_OUTBOUND_ENABLED": null,
    "MW_ALLOW_ENV_FLAG_OVERRIDE": "false",
    "MW_SAFE_MODE_OVERRIDE": null,
    "MW_AUTOMATION_ENABLED_OVERRIDE": null
}

## Prod worker env vars (full snapshot, PII-safe keys only)
Command: aws lambda get-function-configuration --function-name rp-mw-prod-worker --region us-east-2 --profile rp-admin-prod --query 'Environment.Variables' --output json
{
    "AUTOMATION_ENABLED_PARAM":  "/rp-mw/prod/automation_enabled",
    "MW_AUTOMATION_ENABLED_OVERRIDE":  null,
    "SHOPIFY_OUTBOUND_ENABLED":  null,
    "MW_ALLOW_ENV_FLAG_OVERRIDE":  "false",
    "SAFE_MODE_PARAM":  "/rp-mw/prod/safe_mode",
    "RICHPANEL_READ_ONLY":  null,
    "RICHPANEL_OUTBOUND_ENABLED":  null,
    "RICHPANEL_WRITE_DISABLED":  null,
    "SHOPIFY_WRITE_DISABLED":  null,
    "MW_SAFE_MODE_OVERRIDE":  null,
    "MW_ENV":  "prod"
}

## CloudFormation stacks (prod account)
Command: aws cloudformation list-stacks --region us-east-2 --profile rp-admin-prod --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE UPDATE_ROLLBACK_COMPLETE --output json
{
    "StackSummaries": [
        {
            "StackId": "arn:aws:<redacted>",
            "StackName": "RichpanelMiddleware-prod",
            "TemplateDescription": "Richpanel middleware scaffold (prod)",
            "CreationTime": "2026-01-31T16:40:11.074000+00:00",
            "LastUpdatedTime": "2026-02-02T15:28:25.187000+00:00",
            "StackStatus": "UPDATE_COMPLETE",
            "DriftInformation": {
                "StackDriftStatus": "NOT_CHECKED"
            },
            "LastOperations": [
                {
                    "OperationType": "UPDATE_STACK",
                    "OperationId": "d71eae56-edf2-4f68-b762-7acee5776f15"
                }
            ]
        },
        {
            "StackId": "arn:aws:<redacted>",
            "StackName": "CDKToolkit",
            "TemplateDescription": "This stack includes resources needed to deploy AWS CDK apps into this environment",
            "CreationTime": "2026-01-02T01:37:53.694000+00:00",
            "LastUpdatedTime": "2026-01-02T01:37:59.830000+00:00",
            "StackStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackDriftStatus": "NOT_CHECKED"
            },
            "LastOperations": [
                {
                    "OperationType": "CREATE_STACK",
                    "OperationId": "5ede73c4-9601-437e-9fac-24adaf1351a6"
                }
            ]
        }
    ]
}

## CloudFormation stack outputs (RichpanelMiddleware-prod)
Command: aws cloudformation describe-stacks --stack-name RichpanelMiddleware-prod --region us-east-2 --profile rp-admin-prod --output json
{
    "Stacks": [
        {
            "StackId": "arn:aws:<redacted>",
            "StackName": "RichpanelMiddleware-prod",
            "ChangeSetId": "arn:aws:<redacted>",
            "Description": "Richpanel middleware scaffold (prod)",
            "Parameters": [
                {
                    "ParameterKey": "SafeModeFlagParameterParameter",
                    "ParameterValue": "/rp-mw/prod/safe_mode",
                    "ResolvedValue": "true"
                },
                {
                    "ParameterKey": "AutomationEnabledFlagParameterParameter",
                    "ParameterValue": "/rp-mw/prod/automation_enabled",
                    "ResolvedValue": "false"
                },
                {
                    "ParameterKey": "BootstrapVersion",
                    "ParameterValue": "/cdk-bootstrap/hnb659fds/version",
                    "ResolvedValue": "30"
                }
            ],
            "CreationTime": "2026-01-31T16:40:11.074000+00:00",
            "LastUpdatedTime": "2026-02-02T15:28:25.187000+00:00",
            "RollbackConfiguration": {},
            "StackStatus": "UPDATE_COMPLETE",
            "DisableRollback": false,
            "NotificationARNs": [],
            "Capabilities": [
                "CAPABILITY_IAM",
                "CAPABILITY_NAMED_IAM",
                "CAPABILITY_AUTO_EXPAND"
            ],
            "Outputs": [
                {
                    "OutputKey": "AuditTrailTableName",
                    "OutputValue": "rp_mw_prod_audit_trail",
                    "Description": "DynamoDB table name for audit trail records."
                },
                {
                    "OutputKey": "EventsQueueName",
                    "OutputValue": "rp-mw-prod-events.fifo",
                    "Description": "Primary FIFO queue that decouples ingress and worker lambdas."
                },
                {
                    "OutputKey": "AutomationEnabledParamPath",
                    "OutputValue": "/rp-mw/prod/automation_enabled",
                    "Description": "SSM parameter path for the automation_enabled feature flag."
                },
                {
                    "OutputKey": "IdempotencyTableName",
                    "OutputValue": "rp_mw_prod_idempotency",
                    "Description": "DynamoDB table name for idempotency records."
                },
                {
                    "OutputKey": "SafeModeParamPath",
                    "OutputValue": "/rp-mw/prod/safe_mode",
                    "Description": "SSM parameter path for the safe_mode feature flag."
                },
                {
                    "OutputKey": "IngressEndpointUrl",
                    "OutputValue": "https://<redacted>.execute-api.us-east-2.amazonaws.com",
                    "Description": "Public HTTP API endpoint for webhook ingress."
                },
                {
                    "OutputKey": "EventsQueueUrl",
                    "OutputValue": "https://sqs.us-east-2.amazonaws.com/<redacted>",
                    "Description": "Queue URL for diagnostics and smoke tests."
                },
                {
                    "OutputKey": "SecretsNamespace",
                    "OutputValue": "rp-mw/prod",
                    "Description": "Secrets Manager prefix rp-mw/<env>/..."
                },
                {
                    "OutputKey": "NamespacePrefix",
                    "OutputValue": "/rp-mw/prod",
                    "Description": "Base /rp-mw/<env> prefix for parameters and shared config."
                },
                {
                    "OutputKey": "ConversationStateTableName",
                    "OutputValue": "rp_mw_prod_conversation_state",
                    "Description": "DynamoDB table name for conversation state snapshots."
                }
            ],
            "RoleARN": "arn:aws:<redacted>",
            "Tags": [
                {
                    "Key": "owner",
                    "Value": "middleware"
                },
                {
                    "Key": "tier",
                    "Value": "prod"
                },
                {
                    "Key": "service",
                    "Value": "richpanel-middleware"
                },
                {
                    "Key": "env",
                    "Value": "prod"
                },
                {
                    "Key": "cost-center",
                    "Value": "eng-prod"
                }
            ],
            "EnableTerminationProtection": false,
            "DriftInformation": {
                "StackDriftStatus": "NOT_CHECKED"
            },
            "LastOperations": [
                {
                    "OperationType": "UPDATE_STACK",
                    "OperationId": "d71eae56-edf2-4f68-b762-7acee5776f15"
                }
            ]
        }
    ]
}

## CloudFormation stack resources (RichpanelMiddleware-prod)
[REDACTED: resource list removed to avoid exposing production resource identifiers.]

## CloudFormation template env (worker Lambda, PII-safe extract)
Note: CloudFormation template body is YAML in this account; parsing requires a YAML parser not available in this environment. Lambda env context was captured via aws lambda get-function-configuration above.

