from __future__ import annotations

import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import aws_account_preflight
import secrets_preflight
import sync_bot_agent_secret


class _DummySTSClient:
    def __init__(self, account_id: str) -> None:
        self._account_id = account_id

    def get_caller_identity(self):
        return {"Account": self._account_id}


class _DummySecretsClient:
    def __init__(self, *, missing_ids=None, unreadable_ids=None) -> None:
        self._missing = set(missing_ids or [])
        self._unreadable = set(unreadable_ids or [])
        self.created = []

    def describe_secret(self, SecretId: str):
        if SecretId in self._missing:
            raise RuntimeError("NotFound")
        return {"Name": SecretId}

    def get_secret_value(self, SecretId: str):
        if SecretId in self._unreadable:
            raise RuntimeError("AccessDenied")
        if SecretId in self._missing:
            raise RuntimeError("NotFound")
        return {"SecretString": "redacted"}

    def create_secret(self, *, Name: str, SecretString: str):
        self.created.append((Name, SecretString))
        return {"Name": Name}


class _DummySSMClient:
    def __init__(self, *, missing_names=None) -> None:
        self._missing = set(missing_names or [])

    def describe_parameters(self, *, ParameterFilters):
        name = ParameterFilters[0]["Values"][0]
        if name in self._missing:
            return {"Parameters": []}
        return {"Parameters": [{"Name": name}]}


class _DummyLambdaClient:
    def __init__(self, *, bot_agent_id: str | None) -> None:
        self._bot_agent_id = bot_agent_id

    def get_function_configuration(self, *, FunctionName: str):
        return {
            "Environment": {
                "Variables": {"RICHPANEL_BOT_AGENT_ID": self._bot_agent_id or ""}
            }
        }


class _DummySession:
    def __init__(
        self,
        *,
        account_id: str = "151124909266",
        secrets_client=None,
        ssm_client=None,
        lambda_client=None,
    ) -> None:
        self._account_id = account_id
        self._secrets = secrets_client or _DummySecretsClient()
        self._ssm = ssm_client or _DummySSMClient()
        self._lambda = lambda_client or _DummyLambdaClient(bot_agent_id=None)

    def client(self, service_name: str, region_name=None):
        if service_name == "sts":
            return _DummySTSClient(self._account_id)
        if service_name == "secretsmanager":
            return self._secrets
        if service_name == "ssm":
            return self._ssm
        if service_name == "lambda":
            return self._lambda
        raise ValueError(f"Unexpected service: {service_name}")


class AccountPreflightTests(unittest.TestCase):
    def test_account_preflight_success(self) -> None:
        session = _DummySession(account_id="151124909266")
        with patch.object(aws_account_preflight, "boto3", new=SimpleNamespace()):
            result = aws_account_preflight.run_account_preflight(
                env_name="dev",
                region="us-east-2",
                session=session,
                fail_on_error=False,
            )
        self.assertTrue(result.ok)
        self.assertEqual(result.aws_account_id, "151124909266")

    def test_account_preflight_wrong_account(self) -> None:
        session = _DummySession(account_id="000000000000")
        with patch.object(aws_account_preflight, "boto3", new=SimpleNamespace()):
            result = aws_account_preflight.run_account_preflight(
                env_name="dev",
                region="us-east-2",
                session=session,
                fail_on_error=False,
            )
        self.assertFalse(result.ok)
        self.assertEqual(result.error, "account_mismatch")

    def test_account_preflight_region_mismatch(self) -> None:
        session = _DummySession(account_id="151124909266")
        with patch.object(aws_account_preflight, "boto3", new=SimpleNamespace()):
            result = aws_account_preflight.run_account_preflight(
                env_name="dev",
                region="us-west-1",
                session=session,
                fail_on_error=False,
            )
        self.assertFalse(result.ok)
        self.assertIn("region_mismatch", result.error or "")


class SecretsPreflightTests(unittest.TestCase):
    def test_secrets_preflight_env_override(self) -> None:
        session = _DummySession()
        with patch.object(secrets_preflight, "boto3", new=SimpleNamespace()):
            with patch.object(
                secrets_preflight,
                "run_account_preflight",
                return_value=aws_account_preflight.AccountPreflightResult(
                    env="dev",
                    region="us-east-2",
                    aws_account_id="151124909266",
                    expected_account_id="151124909266",
                    expected_region="us-east-2",
                    ok=True,
                    error=None,
                ),
            ):
                os.environ["RICHPANEL_BOT_AGENT_ID"] = "agent-xyz"
                try:
                    payload = secrets_preflight.run_secrets_preflight(
                        env_name="dev",
                        region="us-east-2",
                        session=session,
                        fail_on_error=False,
                    )
                finally:
                    os.environ.pop("RICHPANEL_BOT_AGENT_ID", None)
        bot_secret = "rp-mw/dev/richpanel/bot_agent_id"
        self.assertEqual(payload["secrets"][bot_secret]["source"], "env:RICHPANEL_BOT_AGENT_ID")

    def test_secrets_preflight_missing_required(self) -> None:
        missing = {"rp-mw/prod/richpanel/api_key"}
        secrets_client = _DummySecretsClient(missing_ids=missing)
        session = _DummySession(secrets_client=secrets_client)
        with patch.object(secrets_preflight, "boto3", new=SimpleNamespace()):
            with patch.object(
                secrets_preflight,
                "run_account_preflight",
                return_value=aws_account_preflight.AccountPreflightResult(
                    env="prod",
                    region="us-east-2",
                    aws_account_id="878145708918",
                    expected_account_id="878145708918",
                    expected_region="us-east-2",
                    ok=True,
                    error=None,
                ),
            ):
                payload = secrets_preflight.run_secrets_preflight(
                    env_name="prod",
                    region="us-east-2",
                    session=session,
                    fail_on_error=False,
                )
        self.assertEqual(payload["overall_status"], "FAIL")
        self.assertIn("rp-mw/prod/richpanel/api_key", payload["failures"]["required_secrets"])


class SyncBotAgentSecretTests(unittest.TestCase):
    def test_sync_bot_agent_secret_skips_when_exists(self) -> None:
        secrets_client = _DummySecretsClient()
        lambda_client = _DummyLambdaClient(bot_agent_id="agent-123")
        session = _DummySession(secrets_client=secrets_client, lambda_client=lambda_client)
        with patch.object(sync_bot_agent_secret, "boto3", new=SimpleNamespace(session=SimpleNamespace(Session=lambda region_name=None: session))):
            result = sync_bot_agent_secret.main_with_args(env="prod", region="us-east-2")
        self.assertEqual(result, 0)
        self.assertEqual(secrets_client.created, [])

    def test_sync_bot_agent_secret_creates_when_missing(self) -> None:
        secrets_client = _DummySecretsClient(missing_ids={"rp-mw/prod/richpanel/bot_agent_id"})
        lambda_client = _DummyLambdaClient(bot_agent_id="agent-123")
        session = _DummySession(secrets_client=secrets_client, lambda_client=lambda_client)
        with patch.object(sync_bot_agent_secret, "boto3", new=SimpleNamespace(session=SimpleNamespace(Session=lambda region_name=None: session))):
            result = sync_bot_agent_secret.main_with_args(env="prod", region="us-east-2")
        self.assertEqual(result, 0)
        self.assertEqual(secrets_client.created[0][0], "rp-mw/prod/richpanel/bot_agent_id")


if __name__ == "__main__":
    raise SystemExit(unittest.main())
