#!/usr/bin/env node
import { App } from "aws-cdk-lib";
import { RichpanelMiddlewareStack } from "../lib/richpanel-middleware-stack";

const app = new App();

new RichpanelMiddlewareStack(app, "RichpanelMiddlewareStack", {
  // env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION },
});

app.synth();
