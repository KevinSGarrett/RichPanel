#!/usr/bin/env node
import { App } from "aws-cdk-lib";
import { RichpanelMiddlewareStack } from "../lib/richpanel-middleware-stack";
import {
  DEPLOYMENT_ENVIRONMENTS,
  EnvironmentOverrides,
  buildEnvironmentMatrix,
  normalizeEnvironmentName,
} from "../lib/environments";

const app = new App();

const envContext = app.node.tryGetContext("env") as string | undefined;
const contextOverrides = (app.node.tryGetContext("environments") ??
  {}) as Record<string, EnvironmentOverrides>;

const environments = buildEnvironmentMatrix(contextOverrides);

const selectedEnvs = envContext
  ? envContext
      .split(",")
      .map((value) => value.trim())
      .filter(Boolean)
      .map((name) => normalizeEnvironmentName(name))
  : DEPLOYMENT_ENVIRONMENTS;

selectedEnvs.forEach((envName) => {
  const envConfig = environments[envName];

  new RichpanelMiddlewareStack(app, `RichpanelMiddleware-${envName}`, {
    environment: envConfig,
    env: {
      account: envConfig.account,
      region: envConfig.region,
    },
    description: `Richpanel middleware scaffold (${envName})`,
  });
});

app.synth();
