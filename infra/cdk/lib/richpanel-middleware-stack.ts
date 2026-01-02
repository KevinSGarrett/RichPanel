import { CfnOutput, Stack, StackProps, Tags } from "aws-cdk-lib";
import { ISecret, Secret } from "aws-cdk-lib/aws-secretsmanager";
import { IStringParameter, StringParameter } from "aws-cdk-lib/aws-ssm";
import { Construct } from "constructs";
import {
  EnvironmentConfig,
  MwNaming,
} from "./environments";

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

/**
 * RichpanelMiddlewareStack (scaffold)
 *
 * Later waves will add:
 * - API Gateway (webhook ingress)
 * - Lambda (ingress ACK-fast)
 * - SQS FIFO + DLQ
 * - Lambda workers
 * - DynamoDB tables (idempotency + minimal state + audit)
 * - Alarms + log retention + dashboards
 */
export class RichpanelMiddlewareStack extends Stack {
  public readonly naming: MwNaming;
  public readonly runtimeFlags: RuntimeFlagParameters;
  public readonly secrets: SecretReferences;

  constructor(
    scope: Construct,
    id: string,
    props: RichpanelMiddlewareStackProps
  ) {
    super(scope, id, props);

    this.naming = new MwNaming(props.environment.name);
    this.runtimeFlags = this.importRuntimeFlagParameters();
    this.secrets = this.importSecretReferences();

    this.applyStandardTags(props.environment);
    this.exposeNamingOutputs();

    // TODO(Wave 04+): add resources per architecture docs.
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
      description:
        "SSM parameter path for the automation_enabled feature flag.",
    });
  }
}
