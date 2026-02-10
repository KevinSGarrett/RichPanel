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
    "Arn": "arn:aws:sts::878145708918:assumed-role/AWSReservedSSO_RP-Deployer_19cf80c2655853f2/rp-deployer-prod"
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
            "StackId": "arn:aws:cloudformation:us-east-2:878145708918:stack/RichpanelMiddleware-prod/825a01e0-fec3-11f0-8031-06844b0d650b",
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
            "StackId": "arn:aws:cloudformation:us-east-2:878145708918:stack/CDKToolkit/a817a180-e77b-11f0-8bd0-0ae0fb530bf1",
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
            "StackId": "arn:aws:cloudformation:us-east-2:878145708918:stack/RichpanelMiddleware-prod/825a01e0-fec3-11f0-8031-06844b0d650b",
            "StackName": "RichpanelMiddleware-prod",
            "ChangeSetId": "arn:aws:cloudformation:us-east-2:878145708918:changeSet/cdk-deploy-change-set/91ae5085-9962-46b5-a7de-3fd5327357db",
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
                    "OutputValue": "https://0rg6x71jw0.execute-api.us-east-2.amazonaws.com",
                    "Description": "Public HTTP API endpoint for webhook ingress."
                },
                {
                    "OutputKey": "EventsQueueUrl",
                    "OutputValue": "https://sqs.us-east-2.amazonaws.com/878145708918/rp-mw-prod-events.fifo",
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
            "RoleARN": "arn:aws:iam::878145708918:role/cdk-hnb659fds-cfn-exec-role-878145708918-us-east-2",
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
Command: aws cloudformation list-stack-resources --stack-name RichpanelMiddleware-prod --region us-east-2 --profile rp-admin-prod --output json
{
    "StackResourceSummaries": [
        {
            "LogicalResourceId": "AuditTrailTable4CEE68C7",
            "PhysicalResourceId": "rp_mw_prod_audit_trail",
            "ResourceType": "AWS::DynamoDB::Table",
            "LastUpdatedTimestamp": "2026-01-31T16:40:34.142000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "LogicalResourceId": "CDKMetadata",
            "PhysicalResourceId": "825a01e0-fec3-11f0-8031-06844b0d650b",
            "ResourceType": "AWS::CDK::Metadata",
            "LastUpdatedTimestamp": "2026-02-02T15:26:34.767000+00:00",
            "ResourceStatus": "UPDATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "LogicalResourceId": "ConversationStateTable35B2104E",
            "PhysicalResourceId": "rp_mw_prod_conversation_state",
            "ResourceType": "AWS::DynamoDB::Table",
            "LastUpdatedTimestamp": "2026-01-31T16:40:34.163000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "LogicalResourceId": "EventsDlqACDA5DFF",
            "PhysicalResourceId": "https://sqs.us-east-2.amazonaws.com/878145708918/rp-mw-prod-events-dlq.fifo",
            "ResourceType": "AWS::SQS::Queue",
            "LastUpdatedTimestamp": "2026-01-31T16:40:51.632000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "LogicalResourceId": "EventsQueueB96EB0D2",
            "PhysicalResourceId": "https://sqs.us-east-2.amazonaws.com/878145708918/rp-mw-prod-events.fifo",
            "ResourceType": "AWS::SQS::Queue",
            "LastUpdatedTimestamp": "2026-01-31T16:40:53.607000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "LogicalResourceId": "IdempotencyTable22A5A209",
            "PhysicalResourceId": "rp_mw_prod_idempotency",
            "ResourceType": "AWS::DynamoDB::Table",
            "LastUpdatedTimestamp": "2026-01-31T16:40:34.106000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "LogicalResourceId": "IngressHttpApi",
            "PhysicalResourceId": "0rg6x71jw0",
            "ResourceType": "AWS::ApiGatewayV2::Api",
            "LastUpdatedTimestamp": "2026-01-31T16:40:21.933000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "LogicalResourceId": "IngressIntegration",
            "PhysicalResourceId": "s1vv1cc",
            "ResourceType": "AWS::ApiGatewayV2::Integration",
            "LastUpdatedTimestamp": "2026-01-31T16:41:06.673000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "LogicalResourceId": "IngressInvokePermission",
            "PhysicalResourceId": "RichpanelMiddleware-prod-IngressInvokePermission-56YzcpgLqAAQ",
            "ResourceType": "AWS::Lambda::Permission",
            "LastUpdatedTimestamp": "2026-01-31T16:41:06.630000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "LogicalResourceId": "IngressLambdaECAF4BFE",
            "PhysicalResourceId": "rp-mw-prod-ingress",
            "ResourceType": "AWS::Lambda::Function",
            "LastUpdatedTimestamp": "2026-02-02T15:26:42.230000+00:00",
            "ResourceStatus": "UPDATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "LogicalResourceId": "IngressLambdaServiceRole7C5BA865",
            "PhysicalResourceId": "RichpanelMiddleware-prod-IngressLambdaServiceRole7C-UTsCHeJtDwL7",
            "ResourceType": "AWS::IAM::Role",
            "LastUpdatedTimestamp": "2026-01-31T16:40:37.518000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "LogicalResourceId": "IngressLambdaServiceRoleDefaultPolicy4FC7C7EC",
            "PhysicalResourceId": "Richp-Ingre-or24wu45f30I",
            "ResourceType": "AWS::IAM::Policy",
            "LastUpdatedTimestamp": "2026-01-31T16:40:54.561000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "LogicalResourceId": "IngressRoute",
            "PhysicalResourceId": "2g8ig4o",
            "ResourceType": "AWS::ApiGatewayV2::Route",
            "LastUpdatedTimestamp": "2026-01-31T16:41:08.786000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "LogicalResourceId": "IngressStage",
            "PhysicalResourceId": "$default",
            "ResourceType": "AWS::ApiGatewayV2::Stage",
            "LastUpdatedTimestamp": "2026-01-31T16:40:23.879000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "LogicalResourceId": "OpenAIIntentFailureAlarm2AB3E8B8",
            "PhysicalResourceId": "rp-mw-prod-openai-intent-failures",
            "ResourceType": "AWS::CloudWatch::Alarm",
            "LastUpdatedTimestamp": "2026-02-02T15:28:32.443000+00:00",
            "ResourceStatus": "UPDATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "LogicalResourceId": "OpenAIIntentFailureMetricFilter10CC4CB6",
            "PhysicalResourceId": "OpenAIIntentFailureMetricFilter10CC4CB6-pbPXIPmzvCqE",
            "ResourceType": "AWS::Logs::MetricFilter",
            "LastUpdatedTimestamp": "2026-02-02T15:26:55.540000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "LogicalResourceId": "OrderStatusMonitoringDashboardCBE11F6D",
            "PhysicalResourceId": "rp-mw-prod-order-status",
            "ResourceType": "AWS::CloudWatch::Dashboard",
            "LastUpdatedTimestamp": "2026-02-02T15:26:45.533000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "LogicalResourceId": "Richpanel429MetricFilterFAB5B1E6",
            "PhysicalResourceId": "Richpanel429MetricFilterFAB5B1E6-cDh5fhs4KQFU",
            "ResourceType": "AWS::Logs::MetricFilter",
            "LastUpdatedTimestamp": "2026-02-02T15:26:55.591000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "LogicalResourceId": "Richpanel429SpikeAlarm59204F84",
            "PhysicalResourceId": "rp-mw-prod-richpanel-429-spike",
            "ResourceType": "AWS::CloudWatch::Alarm",
            "LastUpdatedTimestamp": "2026-02-02T15:28:32.690000+00:00",
            "ResourceStatus": "UPDATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "LogicalResourceId": "Shopify429MetricFilterDDB8F0B9",
            "PhysicalResourceId": "Shopify429MetricFilterDDB8F0B9-6pHl22POf1gn",
            "ResourceType": "AWS::Logs::MetricFilter",
            "LastUpdatedTimestamp": "2026-02-02T15:26:55.656000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "LogicalResourceId": "Shopify429SpikeAlarmDAB85E6D",
            "PhysicalResourceId": "rp-mw-prod-shopify-429-spike",
            "ResourceType": "AWS::CloudWatch::Alarm",
            "LastUpdatedTimestamp": "2026-02-02T15:28:32.582000+00:00",
            "ResourceStatus": "UPDATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "LogicalResourceId": "ShopifyRefreshErrorsAlarm3D6D933E",
            "PhysicalResourceId": "rp-mw-prod-shopify-refresh-errors",
            "ResourceType": "AWS::CloudWatch::Alarm",
            "LastUpdatedTimestamp": "2026-02-02T15:28:32.713000+00:00",
            "ResourceStatus": "UPDATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "LogicalResourceId": "ShopifyTokenRefreshLambda7058498D",
            "PhysicalResourceId": "rp-mw-prod-shopify-token-refresh",
            "ResourceType": "AWS::Lambda::Function",
            "LastUpdatedTimestamp": "2026-02-02T15:26:42.424000+00:00",
            "ResourceStatus": "UPDATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "LogicalResourceId": "ShopifyTokenRefreshLambdaServiceRole23095842",
            "PhysicalResourceId": "RichpanelMiddleware-prod-ShopifyTokenRefreshLambdaS-b46zeILuEMZh",
            "ResourceType": "AWS::IAM::Role",
            "LastUpdatedTimestamp": "2026-01-31T16:40:37.425000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "LogicalResourceId": "ShopifyTokenRefreshLambdaServiceRoleDefaultPolicyD883F004",
            "PhysicalResourceId": "Richp-Shopi-MBgTDTGPfmnx",
            "ResourceType": "AWS::IAM::Policy",
            "LastUpdatedTimestamp": "2026-01-31T16:40:54.198000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "LogicalResourceId": "ShopifyTokenRefreshScheduleAllowEventRuleRichpanelMiddlewareprodShopifyTokenRefreshLambda0C1BA96943930087",
            "PhysicalResourceId": "RichpanelMiddleware-prod-ShopifyTokenRefreshScheduleAllowEventRuleRichpanelMiddlewarepr-LK5PNNKiyNJ8",
            "ResourceType": "AWS::Lambda::Permission",
            "LastUpdatedTimestamp": "2026-01-31T16:42:09.202000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "LogicalResourceId": "ShopifyTokenRefreshScheduleEAF710E0",
            "PhysicalResourceId": "RichpanelMiddleware-prod-ShopifyTokenRefreshSchedul-8YOnEPphDps7",
            "ResourceType": "AWS::Events::Rule",
            "LastUpdatedTimestamp": "2026-01-31T16:42:06.970000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "LogicalResourceId": "WorkerErrorRateAlarmE50E54B6",
            "PhysicalResourceId": "rp-mw-prod-worker-error-rate",
            "ResourceType": "AWS::CloudWatch::Alarm",
            "LastUpdatedTimestamp": "2026-02-02T15:28:32.598000+00:00",
            "ResourceStatus": "UPDATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "LogicalResourceId": "WorkerLambdaBD11C0E2",
            "PhysicalResourceId": "rp-mw-prod-worker",
            "ResourceType": "AWS::Lambda::Function",
            "LastUpdatedTimestamp": "2026-02-02T15:26:42.179000+00:00",
            "ResourceStatus": "UPDATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "LogicalResourceId": "WorkerLambdaServiceRole33A0380F",
            "PhysicalResourceId": "RichpanelMiddleware-prod-WorkerLambdaServiceRole33A-SKcKFfYRiQy2",
            "ResourceType": "AWS::IAM::Role",
            "LastUpdatedTimestamp": "2026-01-31T16:40:37.712000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "LogicalResourceId": "WorkerLambdaServiceRoleDefaultPolicyFC3707DA",
            "PhysicalResourceId": "Richp-Worke-jqgpsexAskdD",
            "ResourceType": "AWS::IAM::Policy",
            "LastUpdatedTimestamp": "2026-01-31T16:40:55.948000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "LogicalResourceId": "WorkerLambdaSqsEventSourceRichpanelMiddlewareprodEventsQueueF041E54DD4442BB4",
            "PhysicalResourceId": "cbb320cd-7b3e-4196-ab8b-b60da27eb157",
            "ResourceType": "AWS::Lambda::EventSourceMapping",
            "LastUpdatedTimestamp": "2026-01-31T16:41:19.336000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "LogicalResourceId": "WorkerLogGroup31FDBE4A",
            "PhysicalResourceId": "/aws/lambda/rp-mw-prod-worker",
            "ResourceType": "AWS::Logs::LogGroup",
            "LastUpdatedTimestamp": "2026-02-02T15:26:52.541000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        }
    ]
}

## CloudFormation template env (worker Lambda, PII-safe extract)
Command: aws cloudformation get-template --stack-name RichpanelMiddleware-prod --region us-east-2 --profile rp-admin-prod --output json (extract worker env)
ERROR: aws cloudformation get-template failed: Invalid JSON primitive: .

## CloudFormation template env (worker Lambda, PII-safe extract) - retry
Command: aws cloudformation get-template --stack-name RichpanelMiddleware-prod --region us-east-2 --profile rp-admin-prod --query 'TemplateBody' --output text (extract worker env)
ERROR: aws cloudformation get-template failed: Invalid JSON primitive: Richpanel.

## CloudFormation template env (worker Lambda, PII-safe extract) - python parse v2
Command: aws cloudformation get-template --stack-name RichpanelMiddleware-prod --region us-east-2 --profile rp-admin-prod --query TemplateBody --output text (python parse)
ERROR: TemplateBody is not JSON (likely YAML); unable to parse without yaml module.
TemplateBody snippet (first 500 chars):
﻿Richpanel middleware scaffold (prod) AUDITTRAILTABLENAME	DynamoDB table name for audit trail records. VALUE	AuditTrailTable4CEE68C7 AUTOMATIONENABLEDPARAMPATH	SSM parameter path for the automation_enabled feature flag.	/rp-mw/prod/automation_enabled CONVERSATIONSTATETABLENAME	DynamoDB table name for conversation state snapshots. VALUE	ConversationStateTable35B2104E EVENTSQUEUENAME	Primary FIFO queue that decouples ingress and worker lambdas. FN::GETATT	EventsQueueB96EB0D2 FN::GETATT	QueueName E

## CloudFormation template env (worker Lambda, PII-safe extract) - python parse v3
Command: aws cloudformation get-template --stack-name RichpanelMiddleware-prod --region us-east-2 --profile rp-admin-prod --query TemplateBody --output text (python parse)
ERROR: TemplateBody is not JSON dict (likely YAML or unsupported format).
TemplateBody snippet (first 500 chars):
﻿Richpanel middleware scaffold (prod) AUDITTRAILTABLENAME	DynamoDB table name for audit trail records. VALUE	AuditTrailTable4CEE68C7 AUTOMATIONENABLEDPARAMPATH	SSM parameter path for the automation_enabled feature flag.	/rp-mw/prod/automation_enabled CONVERSATIONSTATETABLENAME	DynamoDB table name for conversation state snapshots. VALUE	ConversationStateTable35B2104E EVENTSQUEUENAME	Primary FIFO queue that decouples ingress and worker lambdas. FN::GETATT	EventsQueueB96EB0D2 FN::GETATT	QueueName E
