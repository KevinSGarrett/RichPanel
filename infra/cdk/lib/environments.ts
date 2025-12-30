export type DeploymentEnvironmentName = "dev" | "staging" | "prod";

export interface EnvironmentSettings {
  readonly account: string;
  readonly region: string;
  readonly owner?: string;
  readonly costCenter?: string;
  readonly tags?: Record<string, string>;
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
    account: "111122223333",
    region: "us-east-2",
    owner: "middleware",
    costCenter: "eng-dev",
    tags: { ...SHARED_TAGS, tier: "dev" },
  },
  staging: {
    account: "444455556666",
    region: "us-east-2",
    owner: "middleware",
    costCenter: "eng-staging",
    tags: { ...SHARED_TAGS, tier: "staging" },
  },
  prod: {
    account: "777788889999",
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
}

