#!/usr/bin/env python3
"""
dev_e2e_smoke.py

End-to-end smoke test for the dev Richpanel middleware stack.

High-level flow:
1. Discover the HTTP endpoint + queue via CloudFormation stack outputs.
2. Fetch the webhook authentication token from Secrets Manager.
3. Send a synthetic webhook payload to the ingress endpoint.
4. Wait for the worker Lambda to persist the event in the DynamoDB idempotency table.
5. Verify the conversation state + audit trail records were written.
6. Emit evidence URLs (API endpoint, SQS queue, DynamoDB tables, CloudWatch log group).

Design constraints:
- Only prints derived identifiers (event_id, queue URL, etc.); never prints secret values.
- Standard library + boto3 only to keep the runtime lightweight on GitHub runners.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    import boto3  # type: ignore
    from boto3.dynamodb.conditions import Key  # type: ignore
    from botocore.exceptions import BotoCoreError, ClientError  # type: ignore
except ImportError as exc:  # pragma: no cover - enforced in CI
    raise SystemExit(
        "boto3 is required to run dev_e2e_smoke.py; install it with `pip install boto3`."
    ) from exc


class SmokeFailure(RuntimeError):
    """Raised when the dev E2E smoke test cannot complete successfully."""


@dataclass
class StackArtifacts:
    endpoint_url: str
    queue_url: str
    secrets_namespace: str
    idempotency_table: str
    conversation_state_table: Optional[str] = None
    audit_trail_table: Optional[str] = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Richpanel dev environment end-to-end smoke test."
    )
    parser.add_argument("--env", default="dev", help="Target environment name (default: dev).")
    parser.add_argument(
        "--region", required=True, help="AWS region that hosts the stack (e.g. us-east-2)."
    )
    parser.add_argument(
        "--stack-name",
        default="RichpanelMiddleware-dev",
        help="CloudFormation stack name to read outputs from.",
    )
    parser.add_argument(
        "--idempotency-table",
        help="Optional override for the DynamoDB idempotency table name. "
        "Defaults to rp_mw_<env>_idempotency.",
    )
    parser.add_argument(
        "--event-id",
        help="Optional event_id to embed in the synthetic payload for easier correlation.",
    )
    parser.add_argument(
        "--summary-path",
        help="Optional file path (e.g. $GITHUB_STEP_SUMMARY) to append a Markdown summary.",
    )
    parser.add_argument(
        "--wait-seconds",
        type=int,
        default=60,
        help="How long to wait for the DynamoDB record before failing (default: 60).",
    )
    return parser.parse_args()


def load_stack_artifacts(
    cfn_client,
    sqs_client,
    apigwv2_client,
    stack_name: str,
    env_name: str,
    region: str,
) -> StackArtifacts:
    try:
        response = cfn_client.describe_stacks(StackName=stack_name)
    except ClientError as exc:
        raise SmokeFailure(f"Unable to describe stack '{stack_name}': {exc}") from exc

    stacks = response.get("Stacks", [])
    if not stacks:
        raise SmokeFailure(f"Stack '{stack_name}' was not found.")

    outputs = {item["OutputKey"]: item["OutputValue"] for item in stacks[0].get("Outputs", [])}

    endpoint = outputs.get("IngressEndpointUrl")
    queue_url = outputs.get("EventsQueueUrl")
    secrets_namespace = outputs.get("SecretsNamespace")
    idempotency_table = outputs.get("IdempotencyTableName")
    conversation_state_table = outputs.get("ConversationStateTableName")
    audit_trail_table = outputs.get("AuditTrailTableName")

    missing_outputs: List[str] = []

    if not endpoint:
        endpoint = derive_ingress_endpoint(
            cfn_client, apigwv2_client, stack_name, env_name, region
        )
        missing_outputs.append("IngressEndpointUrl")

    if not queue_url:
        queue_url = derive_queue_url(sqs_client, env_name)
        missing_outputs.append("EventsQueueUrl")

    if not secrets_namespace:
        secrets_namespace = infer_secrets_namespace(env_name)
        missing_outputs.append("SecretsNamespace")
    if not idempotency_table:
        idempotency_table = f"rp_mw_{env_name}_idempotency"
        missing_outputs.append("IdempotencyTableName")

    if missing_outputs:
        print(
            "[WARN] Missing stack outputs: "
            f"{', '.join(missing_outputs)}; derived fallback values were used."
        )

    if endpoint:
        endpoint = endpoint.rstrip("/")

    return StackArtifacts(
        endpoint_url=endpoint,
        queue_url=queue_url,
        secrets_namespace=secrets_namespace,
        idempotency_table=idempotency_table,
        conversation_state_table=conversation_state_table,
        audit_trail_table=audit_trail_table,
    )


def build_http_api_endpoint(api_id: str, region: str) -> str:
    return f"https://{api_id}.execute-api.{region}.amazonaws.com"


def derive_ingress_endpoint(
    cfn_client, apigwv2_client, stack_name: str, env_name: str, region: str
) -> str:
    try:
        resources = cfn_client.describe_stack_resources(StackName=stack_name)
    except ClientError as exc:
        print(f"[WARN] Unable to describe stack resources for '{stack_name}': {exc}")
        resources = {}

    stack_resources = resources.get("StackResources", [])

    for resource in stack_resources:
        logical_id = resource.get("LogicalResourceId", "")
        resource_type = resource.get("ResourceType", "")
        if logical_id == "IngressHttpApi" or resource_type == "AWS::ApiGatewayV2::Api":
            api_id = resource.get("PhysicalResourceId")
            if api_id:
                return build_http_api_endpoint(api_id, region)

    for resource in stack_resources:
        if resource.get("ResourceType") == "AWS::ApiGatewayV2::Stage":
            stage_id = resource.get("PhysicalResourceId", "")
            if stage_id:
                delimiter = "/" if "/" in stage_id else ":"
                api_id = stage_id.split(delimiter, 1)[0]
                if api_id:
                    return build_http_api_endpoint(api_id, region)

    target_name = f"rp-mw-{env_name}-ingress"
    available_api_names: List[str] = []
    try:
        paginator = apigwv2_client.get_paginator("get_apis")
        for page in paginator.paginate():
            for api in page.get("Items", []):
                available_api_names.append(api.get("Name", "<unnamed>"))
                name = (api.get("Name") or "").lower()
                canonical_target = target_name.lower()
                if (
                    name == canonical_target
                    or (name.startswith(f"rp-mw-{env_name}") and "ingress" in name)
                    or ("rp-mw" in name and env_name in name and "ingress" in name)
                ):
                    endpoint = api.get("ApiEndpoint")
                    if endpoint:
                        return endpoint.rstrip("/")
                    api_id = api.get("ApiId")
                    if api_id:
                        return build_http_api_endpoint(api_id, region)
    except ClientError as exc:
        raise SmokeFailure(f"Unable to enumerate HTTP APIs in region {region}: {exc}") from exc

    resource_summary = ", ".join(
        f"{res.get('LogicalResourceId','<unknown>')} ({res.get('ResourceType','?')})"
        for res in stack_resources
    )
    print(
        f"[WARN] Unable to discover ingress API in stack '{stack_name}'. "
        f"Resources inspected: {resource_summary or 'none'}."
    )
    if available_api_names:
        print(
            "[WARN] HTTP APIs visible via apigatewayv2: "
            + ", ".join(available_api_names)
        )

    raise SmokeFailure(
        "IngressEndpointUrl output missing and HTTP API could not be discovered via CloudFormation or API Gateway."
    )


def derive_queue_url(sqs_client, env_name: str) -> str:
    queue_name = f"rp-mw-{env_name}-events.fifo"
    try:
        response = sqs_client.get_queue_url(QueueName=queue_name)
    except ClientError as exc:
        raise SmokeFailure(
            f"Could not resolve queue URL for '{queue_name}': {exc}"
        ) from exc

    return response["QueueUrl"]


def infer_secrets_namespace(env_name: str) -> str:
    return f"rp-mw/{env_name}"


def load_webhook_token(secrets_client, namespace: str) -> str:
    secret_name = f"{namespace}/richpanel/webhook_token"
    try:
        response = secrets_client.get_secret_value(SecretId=secret_name)
    except ClientError as exc:
        raise SmokeFailure(f"Unable to read webhook token secret '{secret_name}': {exc}") from exc

    if "SecretString" in response and response["SecretString"]:
        return response["SecretString"]

    if "SecretBinary" in response and response["SecretBinary"]:
        return base64.b64decode(response["SecretBinary"]).decode("utf-8")

    raise SmokeFailure(f"Secret '{secret_name}' did not contain a value.")


def send_webhook(endpoint: str, token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    target_url = f"{endpoint}/webhook"
    data = json.dumps(payload).encode("utf-8")
    req = Request(
        url=target_url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "x-richpanel-webhook-token": token,
        },
    )

    try:
        with urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8") or "{}"
            parsed = json.loads(body)
            status_code = resp.getcode()
    except HTTPError as exc:
        detail = exc.read().decode("utf-8")
        raise SmokeFailure(
            f"Webhook request failed with status {exc.code}: {detail or exc.reason}"
        ) from exc
    except URLError as exc:
        raise SmokeFailure(f"Webhook request could not reach {target_url}: {exc.reason}") from exc

    if status_code != 200 or parsed.get("status") != "accepted":
        raise SmokeFailure(
            f"Webhook response was not accepted (status={status_code}, body={parsed})."
        )

    return parsed


def wait_for_dynamodb_record(
    ddb_resource,
    table_name: str,
    event_id: str,
    timeout_seconds: int,
    poll_interval: int = 5,
) -> Dict[str, Any]:
    table = ddb_resource.Table(table_name)
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        try:
            response = table.get_item(Key={"event_id": event_id})
        except (BotoCoreError, ClientError) as exc:
            raise SmokeFailure(f"Failed to query DynamoDB table '{table_name}': {exc}") from exc

        item = response.get("Item")
        if item:
            return item

        time.sleep(poll_interval)

    raise SmokeFailure(
        f"Event '{event_id}' was not observed in table '{table_name}' within {timeout_seconds}s."
    )


def validate_idempotency_item(item: Dict[str, Any]) -> None:
    required = ["event_id", "mode", "safe_mode", "automation_enabled", "payload_excerpt", "status"]
    missing = [key for key in required if key not in item]
    if missing:
        raise SmokeFailure(f"Idempotency item missing required fields: {', '.join(missing)}")
    if not str(item.get("payload_excerpt", "")):
        raise SmokeFailure("Idempotency item payload_excerpt was empty.")


def wait_for_conversation_state_record(
    ddb_resource,
    table_name: str,
    conversation_id: str,
    timeout_seconds: int,
    poll_interval: int = 5,
) -> Dict[str, Any]:
    table = ddb_resource.Table(table_name)
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        try:
            response = table.get_item(Key={"conversation_id": conversation_id})
        except (BotoCoreError, ClientError) as exc:
            raise SmokeFailure(
                f"Failed to query conversation state table '{table_name}': {exc}"
            ) from exc

        item = response.get("Item")
        if item:
            return item

        time.sleep(poll_interval)

    raise SmokeFailure(
        f"Conversation '{conversation_id}' was not observed in table '{table_name}' within {timeout_seconds}s."
    )


def wait_for_audit_record(
    ddb_resource,
    table_name: str,
    conversation_id: str,
    event_id: str,
    timeout_seconds: int,
    poll_interval: int = 5,
) -> Dict[str, Any]:
    table = ddb_resource.Table(table_name)
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        try:
            response = table.query(
                KeyConditionExpression=Key("conversation_id").eq(conversation_id),
                Limit=5,
                ScanIndexForward=False,
            )
        except (BotoCoreError, ClientError) as exc:
            raise SmokeFailure(f"Failed to query audit table '{table_name}': {exc}") from exc

        items = response.get("Items") or []
        for item in items:
            if item.get("event_id") == event_id:
                return item

        time.sleep(poll_interval)

    raise SmokeFailure(
        f"Audit record for event '{event_id}' was not observed in table '{table_name}' within {timeout_seconds}s."
    )


def build_payload(event_id: Optional[str]) -> Dict[str, Any]:
    return {
        "event_id": event_id or f"evt:{uuid.uuid4()}",
        "conversation_id": f"conv-{uuid.uuid4().hex[:8]}",
        "message_id": uuid.uuid4().hex,
        "source": "dev_e2e_smoke",
        "received_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "payload": {
            "type": "smoke_test",
            "agent": "dev_e2e_smoke.py",
            "nonce": uuid.uuid4().hex,
        },
    }


def append_summary(path: str, *, env_name: str, data: Dict[str, Any]) -> None:
    env_label = env_name.strip() or "dev"
    # Title-case the environment label without mutating characters like hyphens.
    env_heading = env_label.replace("_", " ").title()
    lines = [
        f"## {env_heading} E2E Smoke",
        f"- Event ID: `{data['event_id']}`",
        f"- Endpoint: {data['endpoint']}/webhook",
        f"- Queue URL: {data['queue_url']}",
        f"- Idempotency record observed in `{data['ddb_table']}` "
        f"(mode={data['idempotency_mode']}, status={data['idempotency_status']})",
        f"- Idempotency table: `{data['ddb_table']}`",
        f"- Idempotency console: {data['ddb_console_url']}",
        f"- Log group: `{data['logs_group']}`",
        f"- CloudWatch logs: {data['logs_console_url']}",
    ]
    if data.get("conversation_state_table"):
        lines.append(
            "- Conversation state record observed for "
            f"`{data['conversation_id']}` in `{data['conversation_state_table']}`"
        )
        lines.append(f"- Conversation state console: {data['conversation_state_console']}")
    if data.get("audit_trail_table"):
        audit_sort_key = data.get("audit_sort_key") or "n/a"
        lines.append(
            "- Audit record observed for "
            f"`{data['conversation_id']}` (sort_key={audit_sort_key}) "
            f"in `{data['audit_trail_table']}`"
        )
        lines.append(f"- Audit console: {data['audit_console']}")
    lines.append(f"- CloudWatch dashboard: `{data['dashboard_name']}`")
    alarms = data.get("alarm_names") or []
    if alarms:
        lines.append(f"- CloudWatch alarms: {', '.join(f'`{name}`' for name in alarms)}")
    else:
        lines.append("- CloudWatch alarms: none surfaced")
    with open(path, "a", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
        handle.write("\n")


def build_console_links(
    *,
    region: str,
    idempotency_table: str,
    env_name: str,
    conversation_state_table: Optional[str] = None,
    audit_trail_table: Optional[str] = None,
) -> Dict[str, str]:
    ddb_console = (
        f"https://{region}.console.aws.amazon.com/dynamodbv2/home"
        f"?region={region}#item-explorer?initialTagKey=&initialTagValue=&table={idempotency_table}"
    )
    conversation_console = None
    audit_console = None
    if conversation_state_table:
        conversation_console = (
            f"https://{region}.console.aws.amazon.com/dynamodbv2/home"
            f"?region={region}#item-explorer?initialTagKey=&initialTagValue=&table={conversation_state_table}"
        )
    if audit_trail_table:
        audit_console = (
            f"https://{region}.console.aws.amazon.com/dynamodbv2/home"
            f"?region={region}#item-explorer?initialTagKey=&initialTagValue=&table={audit_trail_table}"
        )
    logs_group = f"/aws/lambda/rp-mw-{env_name}-worker"
    logs_console = (
        f"https://{region}.console.aws.amazon.com/cloudwatch/home"
        f"?region={region}#logsV2:log-groups/log-group/{logs_group.replace('/', '$252F')}"
    )
    return {
        "ddb": ddb_console,
        "logs": logs_console,
        "log_group": logs_group,
        "conversation_ddb": conversation_console,
        "audit_ddb": audit_console,
    }


def main() -> int:
    args = parse_args()
    region = args.region
    env_name = args.env
    default_idempotency_table = f"rp_mw_{env_name}_idempotency"

    print(f"[INFO] Target stack: {args.stack_name} (region={region}, env={env_name})")

    session = boto3.session.Session(region_name=region)
    cfn_client = session.client("cloudformation")
    sqs_client = session.client("sqs")
    apigwv2_client = session.client("apigatewayv2")
    secrets_client = session.client("secretsmanager")
    ddb_resource = session.resource("dynamodb")

    artifacts = load_stack_artifacts(
        cfn_client,
        sqs_client,
        apigwv2_client,
        args.stack_name,
        env_name,
        region,
    )
    dynamo_table = args.idempotency_table or artifacts.idempotency_table or default_idempotency_table
    if not artifacts.conversation_state_table:
        raise SmokeFailure("ConversationStateTableName output was missing from the stack.")
    if not artifacts.audit_trail_table:
        raise SmokeFailure("AuditTrailTableName output was missing from the stack.")

    console_links = build_console_links(
        region=region,
        idempotency_table=dynamo_table,
        env_name=env_name,
        conversation_state_table=artifacts.conversation_state_table,
        audit_trail_table=artifacts.audit_trail_table,
    )

    print(f"[INFO] Ingress endpoint: {artifacts.endpoint_url}/webhook")
    print(f"[INFO] Events queue URL: {artifacts.queue_url}")
    print(f"[INFO] Secrets namespace: {artifacts.secrets_namespace}")

    token = load_webhook_token(secrets_client, artifacts.secrets_namespace)

    payload = build_payload(args.event_id)
    event_id = payload["event_id"]
    print(f"[INFO] Sending synthetic webhook with event_id={event_id}")

    response = send_webhook(artifacts.endpoint_url, token, payload)
    returned_event_id = response.get("event_id")
    if returned_event_id and returned_event_id != event_id:
        raise SmokeFailure(
            f"Webhook response event_id mismatch (got={returned_event_id}, expected={event_id})."
        )

    print("[INFO] Webhook accepted, waiting for DynamoDB record...")
    item = wait_for_dynamodb_record(
        ddb_resource,
        table_name=dynamo_table,
        event_id=event_id,
        timeout_seconds=args.wait_seconds,
    )
    validate_idempotency_item(item)
    mode = item.get("mode")
    print(f"[OK] Event '{event_id}' observed in table '{dynamo_table}' (mode={mode}).")
    print(f"[INFO] DynamoDB console: {console_links['ddb']}")
    conversation_id = item.get("conversation_id") or payload["conversation_id"]

    state_item = wait_for_conversation_state_record(
        ddb_resource,
        table_name=artifacts.conversation_state_table,
        conversation_id=conversation_id,
        timeout_seconds=args.wait_seconds,
    )
    print(
        f"[OK] Conversation state written for '{conversation_id}' "
        f"in '{artifacts.conversation_state_table}'."
    )

    audit_item = wait_for_audit_record(
        ddb_resource,
        table_name=artifacts.audit_trail_table,
        conversation_id=conversation_id,
        event_id=event_id,
        timeout_seconds=args.wait_seconds,
    )
    print(
        f"[OK] Audit record written for '{conversation_id}' "
        f"in '{artifacts.audit_trail_table}'."
    )
    print(f"[INFO] CloudWatch logs group: {console_links['log_group']}")
    print(f"[INFO] Logs console: {console_links['logs']}")

    dashboard_name = f"rp-mw-{env_name}-ops"
    alarm_names = [
        f"rp-mw-{env_name}-dlq-depth",
        f"rp-mw-{env_name}-worker-errors",
        f"rp-mw-{env_name}-worker-throttles",
        f"rp-mw-{env_name}-ingress-errors",
    ]

    summary_data = {
        "event_id": event_id,
        "endpoint": artifacts.endpoint_url,
        "queue_url": artifacts.queue_url,
        "ddb_table": dynamo_table,
        "ddb_console_url": console_links["ddb"],
        "logs_console_url": console_links["logs"],
        "logs_group": console_links["log_group"],
        "conversation_state_table": artifacts.conversation_state_table,
        "conversation_state_console": console_links["conversation_ddb"],
        "audit_trail_table": artifacts.audit_trail_table,
        "audit_console": console_links["audit_ddb"],
        "conversation_id": conversation_id,
        "idempotency_status": item.get("status", "observed"),
        "idempotency_mode": mode or "unknown",
        "audit_sort_key": audit_item.get("ts_action_id"),
        "dashboard_name": dashboard_name,
        "alarm_names": alarm_names,
    }
    if args.summary_path:
        append_summary(args.summary_path, env_name=env_name, data=summary_data)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SmokeFailure as exc:
        print(f"[FAIL] Dev E2E smoke test failed: {exc}")
        raise SystemExit(1)

