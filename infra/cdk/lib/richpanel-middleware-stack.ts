// infra/cdk/lib/richpanel-middleware-stack.ts

import {
  CfnOutput,
  Duration,
  RemovalPolicy,
  Stack,
  StackProps,
  Tags,
} from "aws-cdk-lib";
import * as apigwv2 from "aws-cdk-lib/aws-apigatewayv2";
import * as cloudwatch from "aws-cdk-lib/aws-cloudwatch";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as events from "aws-cdk-lib/aws-events";
import * as targets from "aws-cdk-lib/aws-events-targets";
import * as lambda from "aws-cdk-lib/aws-lambda";
import { SqsEventSource } from "aws-cdk-lib/aws-lambda-event-sources";
import * as logs from "aws-cdk-lib/aws-logs";
import { ISecret, Secret } from "aws-cdk-lib/aws-secretsmanager";
import { IStringParameter, StringParameter } from "aws-cdk-lib/aws-ssm";
import * as sqs from "aws-cdk-lib/aws-sqs";
import { Construct } from "constructs";
import { join } from "path";
import { EnvironmentConfig, MwNaming } from "./environments";
import { existsSync } from "fs";

export interface RichpanelMiddlewareStackProps extends StackProps {
  readonly environment: EnvironmentConfig;
}

export interface RuntimeFlagParameters {
  readonly safeMode: IStringParameter;
  readonly automationEnabled: IStringParameter;
}

export interface SecretReferences {
  readonly richpanelApiKey: ISecret;
  readonly richpanelWebhookToken: ISecret;
  readonly openaiApiKey: ISecret;
  readonly shopifyAdminApiToken: ISecret;
  readonly shopifyClientId: ISecret;
  readonly shopifyClientSecret: ISecret;
  readonly shopifyRefreshToken: ISecret;
}

interface EventPipelineResources {
  readonly eventsQueue: sqs.Queue;
  readonly httpApiEndpoint: string;

  readonly idempotencyTable: dynamodb.Table;
  readonly conversationStateTable: dynamodb.Table;
  readonly auditTrailTable: dynamodb.Table;
  readonly workerFunction: lambda.Function;
  readonly shopifyRefreshFunction?: lambda.Function;
}

/**
 * RichpanelMiddlewareStack
 *
 * Wave B2 delivers the first runnable pipeline:
 * - HTTP API Gateway ingress endpoint (public)
 * - Ingress Lambda (token validation + enqueue)
 * - SQS FIFO queue (+ DLQ) for serialized events
 * - Worker Lambda subscribed to the queue
 * - DynamoDB idempotency table
 * - DynamoDB conversation state + audit trail tables (for smoke tests + run evidence)
 *
 * Later waves will extend observability, alarms, storage, and automation logic.
 */
export class RichpanelMiddlewareStack extends Stack {
  public readonly naming: MwNaming;
  public readonly runtimeFlags: RuntimeFlagParameters;
  public readonly secrets: SecretReferences;
  private readonly environmentConfig: EnvironmentConfig;

  constructor(
    scope: Construct,
    id: string,
    props: RichpanelMiddlewareStackProps
  ) {
    super(scope, id, props);

    this.environmentConfig = props.environment;
    this.naming = new MwNaming(this.environmentConfig.name);
    this.runtimeFlags = this.importRuntimeFlagParameters();
    this.secrets = this.importSecretReferences();

    this.applyStandardTags(this.environmentConfig);
    const pipeline = this.buildEventPipeline();
    this.addMonitoring(pipeline);
    this.exposeNamingOutputs();
    this.exposePipelineOutputs(pipeline);
  }

  private importRuntimeFlagParameters(): RuntimeFlagParameters {
    return {
      safeMode: StringParameter.fromStringParameterAttributes(
        this,
        "SafeModeFlagParameter",
        {
          parameterName: this.naming.ssmParameter("safe_mode"),
        }
      ),
      automationEnabled: StringParameter.fromStringParameterAttributes(
        this,
        "AutomationEnabledFlagParameter",
        {
          parameterName: this.naming.ssmParameter("automation_enabled"),
        }
      ),
    };
  }

  private importSecretReferences(): SecretReferences {
    return {
      richpanelApiKey: Secret.fromSecretNameV2(
        this,
        "RichpanelApiKeySecret",
        this.naming.secretPath("richpanel", "api_key")
      ),
      richpanelWebhookToken: Secret.fromSecretNameV2(
        this,
        "RichpanelWebhookTokenSecret",
        this.naming.secretPath("richpanel", "webhook_token")
      ),
      openaiApiKey: Secret.fromSecretNameV2(
        this,
        "OpenAiApiKeySecret",
        this.naming.secretPath("openai", "api_key")
      ),
      shopifyAdminApiToken: Secret.fromSecretNameV2(
        this,
        "ShopifyAdminApiTokenSecret",
        this.naming.secretPath("shopify", "admin_api_token")
      ),
      shopifyClientId: Secret.fromSecretNameV2(
        this,
        "ShopifyClientIdSecret",
        this.naming.secretPath("shopify", "client_id")
      ),
      shopifyClientSecret: Secret.fromSecretNameV2(
        this,
        "ShopifyClientSecretSecret",
        this.naming.secretPath("shopify", "client_secret")
      ),
      shopifyRefreshToken: Secret.fromSecretNameV2(
        this,
        "ShopifyRefreshTokenSecret",
        this.naming.secretPath("shopify", "refresh_token")
      ),
    };
  }

  private applyStandardTags(environment: EnvironmentConfig): void {
    Tags.of(this).add("env", environment.name);

    const tags: Record<string, string | undefined> = {
      owner: environment.owner,
      "cost-center": environment.costCenter,
      ...(environment.tags ?? {}),
    };

    Object.entries(tags).forEach(([key, value]) => {
      if (value) {
        Tags.of(this).add(key, value);
      }
    });
  }

  private buildEventPipeline(): EventPipelineResources {
    /**
     * IMPORTANT PACKAGING NOTE:
     * We package backend/src so that Lambda has BOTH:
     * - lambda_handlers/* (entrypoints)
     * - richpanel_middleware/* and integrations/* (imports used by handlers)
     *
     * If we package only lambda_handlers/ingress or lambda_handlers/worker,
     * imports like `from richpanel_middleware...` will fail at init time and
     * API Gateway will return generic 500s.
     */
    const lambdaSourceRoot = this.resolveRepoPath("backend", "src");

    const deadLetterQueue = new sqs.Queue(this, "EventsDlq", {
      queueName: this.naming.queueName("events-dlq", { fifo: true }),
      fifo: true,
      contentBasedDeduplication: true,
      retentionPeriod: Duration.days(4),
    });

    const eventsQueue = new sqs.Queue(this, "EventsQueue", {
      queueName: this.naming.queueName("events", { fifo: true }),
      fifo: true,
      contentBasedDeduplication: true,
      visibilityTimeout: Duration.seconds(90),
      deadLetterQueue: {
        queue: deadLetterQueue,
        maxReceiveCount: 5,
      },
    });

    const idempotencyTable = new dynamodb.Table(this, "IdempotencyTable", {
      tableName: this.naming.tableName("idempotency"),
      partitionKey: {
        name: "event_id",
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: RemovalPolicy.RETAIN,
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: true,
      },
    });

    const conversationStateTable = new dynamodb.Table(
      this,
      "ConversationStateTable",
      {
        tableName: this.naming.tableName("conversation_state"),
        partitionKey: {
          name: "conversation_id",
          type: dynamodb.AttributeType.STRING,
        },
        billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
        removalPolicy: RemovalPolicy.RETAIN,
        pointInTimeRecoverySpecification: {
          pointInTimeRecoveryEnabled: true,
        },
        timeToLiveAttribute: "expires_at",
      }
    );

    const auditTrailTable = new dynamodb.Table(this, "AuditTrailTable", {
      tableName: this.naming.tableName("audit_trail"),
      partitionKey: {
        name: "conversation_id",
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: "ts_action_id",
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: RemovalPolicy.RETAIN,
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: true,
      },
      timeToLiveAttribute: "expires_at",
    });

    const ingressFunction = new lambda.Function(this, "IngressLambda", {
      functionName: this.naming.lambdaFunctionName("ingress"),
      runtime: lambda.Runtime.PYTHON_3_11,

      // NOTE: entrypoint is inside backend/src/lambda_handlers/ingress/handler.py
      handler: "lambda_handlers.ingress.handler.lambda_handler",

      description: "Richpanel webhook ingress handler (token validation + enqueue).",
      timeout: Duration.seconds(5),
      memorySize: 256,
      environment: {
        EVENT_SOURCE: "richpanel_http_target",
        QUEUE_URL: eventsQueue.queueUrl,

        /**
         * Handler expects a Secret identifier it can resolve via Secrets Manager.
         * Passing the SECRET NAME/path is the safest across accounts.
         */
        WEBHOOK_SECRET_ARN: this.naming.secretPath("richpanel", "webhook_token"),

        DEFAULT_MESSAGE_GROUP_ID: `${this.naming.resourcePrefix()}-default`,
      },

      // IMPORTANT: package backend/src (not just the ingress folder)
      code: lambda.Code.fromAsset(lambdaSourceRoot),
    });

    eventsQueue.grantSendMessages(ingressFunction);
    this.secrets.richpanelWebhookToken.grantRead(ingressFunction);

    const workerFunction = new lambda.Function(this, "WorkerLambda", {
      functionName: this.naming.lambdaFunctionName("worker"),
      runtime: lambda.Runtime.PYTHON_3_11,

      // NOTE: entrypoint is inside backend/src/lambda_handlers/worker/handler.py
      handler: "lambda_handlers.worker.handler.lambda_handler",

      description:
        "SQS worker that logs events, enforces kill switches, and writes idempotency records.",
      timeout: Duration.seconds(30),
      memorySize: 512,
      reservedConcurrentExecutions: 1,
      environment: {
        IDEMPOTENCY_TABLE_NAME: idempotencyTable.tableName,
        CONVERSATION_STATE_TABLE_NAME: conversationStateTable.tableName,
        AUDIT_TRAIL_TABLE_NAME: auditTrailTable.tableName,

        SAFE_MODE_PARAM: this.runtimeFlags.safeMode.parameterName,
        AUTOMATION_ENABLED_PARAM: this.runtimeFlags.automationEnabled.parameterName,
        MW_ENV: this.environmentConfig.name,
        MW_ALLOW_ENV_FLAG_OVERRIDE: this.environmentConfig.name === "dev" ? "true" : "false",
        RICHPANEL_API_KEY_SECRET_ARN: this.secrets.richpanelApiKey.secretArn,
        RICHPANEL_RATE_LIMIT_RPS: "0.5",
        SHOPIFY_SHOP_DOMAIN: "scentimen-t.myshopify.com",
        MW_OUTBOUND_ALLOWLIST_EMAILS:
          this.environmentConfig.outboundAllowlistEmails ?? "",
        MW_OUTBOUND_ALLOWLIST_DOMAINS:
          this.environmentConfig.outboundAllowlistDomains ?? "",
        RICHPANEL_BOT_AGENT_ID:
          this.environmentConfig.richpanelBotAuthorId ?? "",
        RICHPANEL_BOT_AUTHOR_ID:
          this.environmentConfig.richpanelBotAuthorId ?? "",
      },

      // IMPORTANT: package backend/src (not just the worker folder)
      code: lambda.Code.fromAsset(lambdaSourceRoot),
    });

    idempotencyTable.grantReadWriteData(workerFunction);
    conversationStateTable.grantReadWriteData(workerFunction);
    auditTrailTable.grantReadWriteData(workerFunction);

    this.runtimeFlags.safeMode.grantRead(workerFunction);
    this.runtimeFlags.automationEnabled.grantRead(workerFunction);
    this.secrets.richpanelApiKey.grantRead(workerFunction);
    this.secrets.openaiApiKey.grantRead(workerFunction);
    this.secrets.shopifyAdminApiToken.grantRead(workerFunction);
    this.secrets.shopifyClientId.grantRead(workerFunction);
    this.secrets.shopifyClientSecret.grantRead(workerFunction);
    this.secrets.shopifyRefreshToken.grantRead(workerFunction);

    workerFunction.addEventSource(
      new SqsEventSource(eventsQueue, {
        batchSize: 1,
        reportBatchItemFailures: true,
      })
    );

    let shopifyRefreshFunction: lambda.Function | undefined;
    if (["prod", "dev"].includes(this.environmentConfig.name)) {
      shopifyRefreshFunction = new lambda.Function(
        this,
        "ShopifyTokenRefreshLambda",
        {
          functionName: this.naming.lambdaFunctionName("shopify-token-refresh"),
          runtime: lambda.Runtime.PYTHON_3_11,
          handler:
            "lambda_handlers.shopify_token_refresh.handler.lambda_handler",
          description:
            "Refresh Shopify admin API access token every 4 hours (read-only ops).",
          timeout: Duration.seconds(30),
          memorySize: 256,
          environment: {
            MW_ENV: this.environmentConfig.name,
            SHOPIFY_SHOP_DOMAIN: "scentimen-t.myshopify.com",
            SHOPIFY_ACCESS_TOKEN_SECRET_ID: this.naming.secretPath(
              "shopify",
              "admin_api_token"
            ),
            SHOPIFY_CLIENT_ID_SECRET_ID: this.naming.secretPath(
              "shopify",
              "client_id"
            ),
            SHOPIFY_CLIENT_SECRET_SECRET_ID: this.naming.secretPath(
              "shopify",
              "client_secret"
            ),
            SHOPIFY_REFRESH_TOKEN_SECRET_ID: this.naming.secretPath(
              "shopify",
              "refresh_token"
            ),
            SHOPIFY_REFRESH_ENABLED: "false",
          },
          code: lambda.Code.fromAsset(lambdaSourceRoot),
        }
      );

      this.secrets.shopifyAdminApiToken.grantRead(shopifyRefreshFunction);
      this.secrets.shopifyAdminApiToken.grantWrite(shopifyRefreshFunction);
      this.secrets.shopifyClientId.grantRead(shopifyRefreshFunction);
      this.secrets.shopifyClientSecret.grantRead(shopifyRefreshFunction);
      this.secrets.shopifyRefreshToken.grantRead(shopifyRefreshFunction);

      const scheduleRule = new events.Rule(
        this,
        "ShopifyTokenRefreshSchedule",
        {
          schedule: events.Schedule.rate(Duration.hours(4)),
        }
      );
      scheduleRule.addTarget(
        new targets.LambdaFunction(shopifyRefreshFunction)
      );
    }

    const httpApi = this.createHttpApi(ingressFunction);

    return {
      eventsQueue,
      httpApiEndpoint: httpApi.attrApiEndpoint,
      idempotencyTable,
      conversationStateTable,
      auditTrailTable,
      workerFunction,
      shopifyRefreshFunction,
    };
  }

  private addMonitoring(pipeline: EventPipelineResources): void {
    const workerLogGroup = new logs.LogGroup(this, "WorkerLogGroup", {
      logGroupName: `/aws/lambda/${pipeline.workerFunction.functionName}`,
      retention: logs.RetentionDays.ONE_MONTH,
      removalPolicy: RemovalPolicy.RETAIN,
    });
    const metricNamespace = this.naming.metricNamespace();

    const workerErrors = pipeline.workerFunction.metricErrors({
      period: Duration.minutes(5),
    });
    const workerInvocations = pipeline.workerFunction.metricInvocations({
      period: Duration.minutes(5),
    });
    const workerErrorRate = new cloudwatch.MathExpression({
      expression: "IF(invocations>0, errors/invocations, 0)",
      usingMetrics: {
        errors: workerErrors,
        invocations: workerInvocations,
      },
      period: Duration.minutes(5),
    });

    new cloudwatch.Alarm(this, "WorkerErrorRateAlarm", {
      alarmName: `${this.naming.resourcePrefix()}-worker-error-rate`,
      alarmDescription:
        "Worker Lambda error rate above baseline (5xx or unhandled errors).",
      metric: workerErrorRate,
      threshold: 0.05,
      evaluationPeriods: 3,
      datapointsToAlarm: 3,
      comparisonOperator:
        cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });

    const richpanel429Metric = new cloudwatch.Metric({
      namespace: metricNamespace,
      metricName: "Richpanel429Count",
      statistic: "sum",
      period: Duration.minutes(5),
    });
    new logs.MetricFilter(this, "Richpanel429MetricFilter", {
      logGroup: workerLogGroup,
      metricNamespace,
      metricName: "Richpanel429Count",
      filterPattern: logs.FilterPattern.allTerms(
        "richpanel.rate_limited",
        "status=429"
      ),
      metricValue: "1",
    });
    new cloudwatch.Alarm(this, "Richpanel429SpikeAlarm", {
      alarmName: `${this.naming.resourcePrefix()}-richpanel-429-spike`,
      alarmDescription: "Richpanel 429 rate-limit spikes.",
      metric: richpanel429Metric,
      threshold: 5,
      evaluationPeriods: 3,
      datapointsToAlarm: 2,
      comparisonOperator:
        cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });

    const shopify429Metric = new cloudwatch.Metric({
      namespace: metricNamespace,
      metricName: "Shopify429Count",
      statistic: "sum",
      period: Duration.minutes(5),
    });
    new logs.MetricFilter(this, "Shopify429MetricFilter", {
      logGroup: workerLogGroup,
      metricNamespace,
      metricName: "Shopify429Count",
      filterPattern: logs.FilterPattern.allTerms(
        "shopify.rate_limited",
        "status=429"
      ),
      metricValue: "1",
    });
    new cloudwatch.Alarm(this, "Shopify429SpikeAlarm", {
      alarmName: `${this.naming.resourcePrefix()}-shopify-429-spike`,
      alarmDescription: "Shopify 429 rate-limit spikes.",
      metric: shopify429Metric,
      threshold: 5,
      evaluationPeriods: 3,
      datapointsToAlarm: 2,
      comparisonOperator:
        cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });

    const openaiFailureMetric = new cloudwatch.Metric({
      namespace: metricNamespace,
      metricName: "OpenAIOrderStatusIntentFailures",
      statistic: "sum",
      period: Duration.minutes(5),
    });
    new logs.MetricFilter(this, "OpenAIIntentFailureMetricFilter", {
      logGroup: workerLogGroup,
      metricNamespace,
      metricName: "OpenAIOrderStatusIntentFailures",
      filterPattern: logs.FilterPattern.allTerms(
        "order_status_intent.request_failed"
      ),
      metricValue: "1",
    });
    new cloudwatch.Alarm(this, "OpenAIIntentFailureAlarm", {
      alarmName: `${this.naming.resourcePrefix()}-openai-intent-failures`,
      alarmDescription: "OpenAI order status intent failures detected.",
      metric: openaiFailureMetric,
      threshold: 0,
      evaluationPeriods: 1,
      comparisonOperator:
        cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });

    if (pipeline.shopifyRefreshFunction) {
      const refreshErrors = pipeline.shopifyRefreshFunction.metricErrors({
        period: Duration.hours(1),
      });
      new cloudwatch.Alarm(this, "ShopifyRefreshErrorsAlarm", {
        alarmName: `${this.naming.resourcePrefix()}-shopify-refresh-errors`,
        alarmDescription:
          "Shopify token refresh Lambda errors > 0 in the last hour.",
        metric: refreshErrors,
        threshold: 0,
        evaluationPeriods: 1,
        comparisonOperator:
          cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
        treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
      });
    }

    const dashboard = new cloudwatch.Dashboard(
      this,
      "OrderStatusMonitoringDashboard",
      {
        dashboardName: `${this.naming.resourcePrefix()}-order-status`,
      }
    );
    dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: "Worker Error Rate",
        left: [workerErrorRate],
      }),
      new cloudwatch.GraphWidget({
        title: "429 Rate Limits",
        left: [richpanel429Metric, shopify429Metric],
      }),
      new cloudwatch.GraphWidget({
        title: "OpenAI Order Status Failures",
        left: [openaiFailureMetric],
      }),
      new cloudwatch.TextWidget({
        markdown:
          "TODO: Wire order_status_true_rate metric once shadow job is scheduled.",
        height: 2,
        width: 24,
      })
    );
  }

  private createHttpApi(ingressFunction: lambda.Function): apigwv2.CfnApi {
    const api = new apigwv2.CfnApi(this, "IngressHttpApi", {
      name: this.naming.apiName("ingress"),
      protocolType: "HTTP",
      corsConfiguration: {
        allowHeaders: ["content-type", "x-richpanel-webhook-token"],
        allowMethods: ["OPTIONS", "POST"],
        allowOrigins: ["*"],
        maxAge: 600,
      },
    });

    const integration = new apigwv2.CfnIntegration(this, "IngressIntegration", {
      apiId: api.ref,
      integrationType: "AWS_PROXY",
      integrationUri: ingressFunction.functionArn,
      payloadFormatVersion: "2.0",
      integrationMethod: "POST",
      timeoutInMillis: 10000,
    });

    new apigwv2.CfnRoute(this, "IngressRoute", {
      apiId: api.ref,
      routeKey: "POST /webhook",
      target: `integrations/${integration.ref}`,
    });

    new apigwv2.CfnStage(this, "IngressStage", {
      apiId: api.ref,
      autoDeploy: true,
      stageName: "$default",
    });

    new lambda.CfnPermission(this, "IngressInvokePermission", {
      action: "lambda:InvokeFunction",
      principal: "apigateway.amazonaws.com",
      functionName: ingressFunction.functionArn,
      sourceArn: `arn:aws:execute-api:${Stack.of(this).region}:${
        Stack.of(this).account
      }:${api.ref}/*/*/*`,
    });

    return api;
  }

  private exposePipelineOutputs(pipeline: EventPipelineResources): void {
    new CfnOutput(this, "IngressEndpointUrl", {
      value: pipeline.httpApiEndpoint,
      description: "Public HTTP API endpoint for webhook ingress.",
    });

    new CfnOutput(this, "EventsQueueName", {
      value: pipeline.eventsQueue.queueName,
      description: "Primary FIFO queue that decouples ingress and worker lambdas.",
    });

    new CfnOutput(this, "EventsQueueUrl", {
      value: pipeline.eventsQueue.queueUrl,
      description: "Queue URL for diagnostics and smoke tests.",
    });

    new CfnOutput(this, "IdempotencyTableName", {
      value: pipeline.idempotencyTable.tableName,
      description: "DynamoDB table name for idempotency records.",
    });

    new CfnOutput(this, "ConversationStateTableName", {
      value: pipeline.conversationStateTable.tableName,
      description: "DynamoDB table name for conversation state snapshots.",
    });

    new CfnOutput(this, "AuditTrailTableName", {
      value: pipeline.auditTrailTable.tableName,
      description: "DynamoDB table name for audit trail records.",
    });
  }

  private resolveRepoPath(...segments: string[]): string {
    const fromSource = join(__dirname, "..", "..", "..", ...segments);
    if (existsSync(fromSource)) {
      return fromSource;
    }

    return join(__dirname, "..", "..", "..", "..", ...segments);
  }

  private exposeNamingOutputs(): void {
    new CfnOutput(this, "NamespacePrefix", {
      value: this.naming.namespace(),
      description: "Base /rp-mw/<env> prefix for parameters and shared config.",
    });

    new CfnOutput(this, "SecretsNamespace", {
      value: this.naming.secretPath(),
      description: "Secrets Manager prefix rp-mw/<env>/...",
    });

    new CfnOutput(this, "SafeModeParamPath", {
      value: this.naming.ssmParameter("safe_mode"),
      description: "SSM parameter path for the safe_mode feature flag.",
    });

    new CfnOutput(this, "AutomationEnabledParamPath", {
      value: this.naming.ssmParameter("automation_enabled"),
      description: "SSM parameter path for the automation_enabled feature flag.",
    });
  }
}
