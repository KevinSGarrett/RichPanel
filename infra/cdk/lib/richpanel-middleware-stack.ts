import { Stack, StackProps } from "aws-cdk-lib";
import { Construct } from "constructs";

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
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    // TODO(Wave 04+): add resources per architecture docs.
  }
}
