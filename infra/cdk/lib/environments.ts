export type DeploymentEnvironmentName = "dev" | "staging" | "prod";

export interface EnvironmentSettings {
  readonly account: string;
  readonly region: string;
  readonly owner?: string;
  readonly costCenter?: string;
  readonly tags?: Record<string, string>;
  readonly outboundAllowlistEmails?: string;
  readonly outboundAllowlistDomains?: string;
  readonly richpanelBotAuthorId?: string;
}

export interface EnvironmentConfig extends EnvironmentSettings {
  readonly name: DeploymentEnvironmentName;
}

export type EnvironmentOverrides = Partial<EnvironmentSettings>;

export const DEPLOYMENT_ENVIRONMENTS: DeploymentEnvironmentName[] = [
  "dev",
  "staging",
  "prod",
];

const SHARED_TAGS = {
  service: "richpanel-middleware",
};

export const DEFAULT_ENVIRONMENTS: Record<
  DeploymentEnvironmentName,
  EnvironmentSettings
> = {
  dev: {
    account: "151124909266",
    region: "us-east-2",
    owner: "middleware",
    costCenter: "eng-dev",
    tags: { ...SHARED_TAGS, tier: "dev" },
  },
  staging: {
    account: "260475105304",
    region: "us-east-2",
    owner: "middleware",
    costCenter: "eng-staging",
    tags: { ...SHARED_TAGS, tier: "staging" },
  },
  prod: {
    account: "878145708918",
    region: "us-east-2",
    owner: "middleware",
    costCenter: "eng-prod",
    tags: { ...SHARED_TAGS, tier: "prod" },
  },
};

export function normalizeEnvironmentName(value: string): DeploymentEnvironmentName {
  const normalized = value?.toLowerCase();
  if (isDeploymentEnvironmentName(normalized)) {
    return normalized;
  }

  throw new Error(
    `Unknown environment "${value}". Expected one of: ${DEPLOYMENT_ENVIRONMENTS.join(
      ", "
    )}`
  );
}

export function isDeploymentEnvironmentName(
  value: string
): value is DeploymentEnvironmentName {
  return (DEPLOYMENT_ENVIRONMENTS as string[]).includes(value);
}

export function buildEnvironmentConfig(
  name: DeploymentEnvironmentName,
  overrides?: EnvironmentOverrides
): EnvironmentConfig {
  const base = DEFAULT_ENVIRONMENTS[name];
  return {
    name,
    account: overrides?.account ?? base.account,
    region: overrides?.region ?? base.region,
    owner: overrides?.owner ?? base.owner,
    costCenter: overrides?.costCenter ?? base.costCenter,
    outboundAllowlistEmails:
      overrides?.outboundAllowlistEmails ?? base.outboundAllowlistEmails,
    outboundAllowlistDomains:
      overrides?.outboundAllowlistDomains ?? base.outboundAllowlistDomains,
    richpanelBotAuthorId:
      overrides?.richpanelBotAuthorId ?? base.richpanelBotAuthorId,
    tags: {
      ...(base.tags ?? {}),
      ...(overrides?.tags ?? {}),
    },
  };
}

export function buildEnvironmentMatrix(
  overrides?: Record<string, EnvironmentOverrides>
): Record<DeploymentEnvironmentName, EnvironmentConfig> {
  return DEPLOYMENT_ENVIRONMENTS.reduce((acc, envName) => {
    const safeOverrides = overrides?.[envName];
    acc[envName] = buildEnvironmentConfig(
      envName,
      safeOverrides as EnvironmentOverrides | undefined
    );
    return acc;
  }, {} as Record<DeploymentEnvironmentName, EnvironmentConfig>);
}

function sanitizeSegment(segment: string): string {
  return segment.replace(/^\/+|\/+$/g, "");
}

export class MwNaming {
  constructor(private readonly env: DeploymentEnvironmentName) {}

  resourcePrefix(): string {
    return `rp-mw-${this.env}`;
  }

  namespace(includeLeadingSlash = true): string {
    const base = `rp-mw/${this.env}`;
    return includeLeadingSlash ? `/${base}` : base;
  }

  ssmParameter(name: string): string {
    return `${this.namespace(true)}/${sanitizeSegment(name)}`;
  }

  secretPath(...segments: string[]): string {
    return [this.namespace(false), ...segments.map(sanitizeSegment)].join("/");
  }

  lambdaLogGroup(functionName: string): string {
    return `/aws/lambda/${this.namespace(false)}/${sanitizeSegment(
      functionName
    )}`;
  }

  metricNamespace(): string {
    return this.namespace(false);
  }

  lambdaFunctionName(name: string): string {
    return `${this.resourcePrefix()}-${sanitizeNameToken(name)}`;
  }

  queueName(name: string, options?: { fifo?: boolean }): string {
    const base = `${this.resourcePrefix()}-${sanitizeNameToken(name)}`;
    return options?.fifo ? `${base}.fifo` : base;
  }

  tableName(name: string): string {
    return `rp_mw_${this.env}_${sanitizeNameToken(name).replace(/-/g, "_")}`;
  }

  apiName(name: string): string {
    return `${this.resourcePrefix()}-${sanitizeNameToken(name)}`;
  }
}

function sanitizeNameToken(segment: string): string {
  const normalized = segment?.trim().toLowerCase() || "component";
  return normalized.replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
}

