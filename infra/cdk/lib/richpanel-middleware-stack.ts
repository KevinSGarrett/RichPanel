import { CfnOutput, Stack, StackProps, Tags } from "aws-cdk-lib";
import { StringParameter } from "aws-cdk-lib/aws-ssm";
import { Construct } from "constructs";
import {
  EnvironmentConfig,
  MwNaming,
} from "./environments";

export interface RichpanelMiddlewareStackProps extends StackProps {
  readonly environment: EnvironmentConfig;
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

  constructor(
    scope: Construct,
    id: string,
    props: RichpanelMiddlewareStackProps
  ) {
    super(scope, id, props);

    this.naming = new MwNaming(props.environment.name);

    this.applyStandardTags(props.environment);
    this.createRuntimeFlagParameters();
    this.exposeNamingOutputs();

    // TODO(Wave 04+): add resources per architecture docs.
  }

  private createRuntimeFlagParameters(): void {
    new StringParameter(this, "SafeModeFlagParameter", {
      parameterName: this.naming.ssmParameter("safe_mode"),
      stringValue: "false",
      description:
        "Route-only kill switch; default false per Kill Switch and Safe Mode runbook.",
    });

    new StringParameter(this, "AutomationEnabledFlagParameter", {
      parameterName: this.naming.ssmParameter("automation_enabled"),
      stringValue: "true",
      description:
        "Global automation kill switch; default true so automation is enabled until toggled.",
    });
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
