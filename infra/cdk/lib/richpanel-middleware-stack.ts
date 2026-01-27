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
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as lambda from "aws-cdk-lib/aws-lambda";
import { SqsEventSource } from "aws-cdk-lib/aws-lambda-event-sources";
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
}

interface EventPipelineResources {
  readonly eventsQueue: sqs.Queue;
  readonly httpApiEndpoint: string;

  readonly idempotencyTable: dynamodb.Table;
  readonly conversationStateTable: dynamodb.Table;
  readonly auditTrailTable: dynamodb.Table;
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
      environment: {
        IDEMPOTENCY_TABLE_NAME: idempotencyTable.tableName,
        CONVERSATION_STATE_TABLE_NAME: conversationStateTable.tableName,
        AUDIT_TRAIL_TABLE_NAME: auditTrailTable.tableName,

        SAFE_MODE_PARAM: this.runtimeFlags.safeMode.parameterName,
        AUTOMATION_ENABLED_PARAM: this.runtimeFlags.automationEnabled.parameterName,
        MW_ENV: this.environmentConfig.name,
        MW_ALLOW_ENV_FLAG_OVERRIDE: this.environmentConfig.name === "dev" ? "true" : "false",
        RICHPANEL_API_KEY_SECRET_ARN: this.secrets.richpanelApiKey.secretArn,
        MW_OUTBOUND_ALLOWLIST_EMAILS:
          this.environmentConfig.outboundAllowlistEmails ?? "",
        MW_OUTBOUND_ALLOWLIST_DOMAINS:
          this.environmentConfig.outboundAllowlistDomains ?? "",
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

    workerFunction.addEventSource(
      new SqsEventSource(eventsQueue, {
        batchSize: 1,
        reportBatchItemFailures: true,
      })
    );

    const httpApi = this.createHttpApi(ingressFunction);

    return {
      eventsQueue,
      httpApiEndpoint: httpApi.attrApiEndpoint,
      idempotencyTable,
      conversationStateTable,
      auditTrailTable,
    };
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
