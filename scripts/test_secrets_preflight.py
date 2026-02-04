from __future__ import annotations

import os
import tempfile
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


class _FailingSTSClient:
    def get_caller_identity(self):
        raise RuntimeError("STS unavailable")


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

    def get_parameter(self, *, Name: str, WithDecryption: bool = False):
        if Name in self._missing:
            raise RuntimeError("ParameterNotFound")
        return {"Parameter": {"Name": Name}}


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
        sts_client=None,
        secrets_client=None,
        ssm_client=None,
        lambda_client=None,
    ) -> None:
        self._account_id = account_id
        self._sts = sts_client
        self._secrets = secrets_client or _DummySecretsClient()
        self._ssm = ssm_client or _DummySSMClient()
        self._lambda = lambda_client or _DummyLambdaClient(bot_agent_id=None)

    def client(self, service_name: str, region_name=None):
        if service_name == "sts":
            return self._sts or _DummySTSClient(self._account_id)
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

    def test_account_preflight_boto3_unavailable(self) -> None:
        with patch.object(aws_account_preflight, "boto3", new=None):
            result = aws_account_preflight.run_account_preflight(
                env_name="dev",
                region="us-east-2",
                session=None,
                fail_on_error=False,
            )
        self.assertEqual(result.error, "boto3_unavailable")
        with patch.object(aws_account_preflight, "boto3", new=None):
            with self.assertRaises(SystemExit):
                aws_account_preflight.run_account_preflight(
                    env_name="dev",
                    region="us-east-2",
                    session=None,
                    fail_on_error=True,
                )

    def test_account_preflight_unknown_env(self) -> None:
        session = _DummySession(account_id="151124909266")
        with patch.object(aws_account_preflight, "boto3", new=SimpleNamespace()):
            result = aws_account_preflight.run_account_preflight(
                env_name="unknown",
                region="us-east-2",
                session=session,
                fail_on_error=False,
            )
        self.assertEqual(result.error, "unknown_env")
        with patch.object(aws_account_preflight, "boto3", new=SimpleNamespace()):
            with self.assertRaises(SystemExit):
                aws_account_preflight.run_account_preflight(
                    env_name="unknown",
                    region="us-east-2",
                    session=session,
                    fail_on_error=True,
                )

    def test_account_preflight_sts_exception(self) -> None:
        session = _DummySession(sts_client=_FailingSTSClient())
        with patch.object(aws_account_preflight, "boto3", new=SimpleNamespace()):
            result = aws_account_preflight.run_account_preflight(
                env_name="dev",
                region="us-east-2",
                session=session,
                fail_on_error=False,
            )
        self.assertEqual(result.error, "RuntimeError")
        with patch.object(aws_account_preflight, "boto3", new=SimpleNamespace()):
            with self.assertRaises(SystemExit):
                aws_account_preflight.run_account_preflight(
                    env_name="dev",
                    region="us-east-2",
                    session=session,
                    fail_on_error=True,
                )

    def test_account_preflight_helpers(self) -> None:
        self.assertEqual(aws_account_preflight.normalize_env("production"), "prod")
        with patch.dict(os.environ, {"AWS_REGION": "us-west-2"}):
            self.assertEqual(aws_account_preflight.resolve_region(None), "us-west-2")
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(aws_account_preflight.resolve_region(None), "us-east-2")

    def test_account_preflight_main(self) -> None:
        with patch.object(
            aws_account_preflight,
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
            with patch("sys.argv", ["aws_account_preflight.py", "--env", "dev"]):
                self.assertEqual(aws_account_preflight.main(), 0)


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

    def test_secrets_preflight_boto3_unavailable(self) -> None:
        with patch.object(secrets_preflight, "boto3", new=None):
            payload = secrets_preflight.run_secrets_preflight(
                env_name="dev",
                region="us-east-2",
                session=None,
                fail_on_error=False,
            )
        self.assertEqual(payload["overall_status"], "FAIL")
        self.assertEqual(payload["error"], "boto3_unavailable")
        self.assertEqual(aws_account_preflight.normalize_env("production"), "prod")

    def test_secrets_preflight_missing_ssm(self) -> None:
        ssm_client = _DummySSMClient(missing_names={"/rp-mw/dev/safe_mode"})
        session = _DummySession(ssm_client=ssm_client)
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
                payload = secrets_preflight.run_secrets_preflight(
                    env_name="dev",
                    region="us-east-2",
                    session=session,
                    fail_on_error=False,
                )
        self.assertIn("/rp-mw/dev/safe_mode", payload["failures"]["required_ssm"])

    def test_secrets_preflight_exception_paths(self) -> None:
        class _FailingSecretsClient(_DummySecretsClient):
            def get_secret_value(self, SecretId: str):
                raise RuntimeError("AccessDenied")

        class _FailingSSMClient(_DummySSMClient):
            def describe_parameters(self, *, ParameterFilters):
                return {"Parameters": [{"Name": ParameterFilters[0]["Values"][0]}]}

            def get_parameter(self, *, Name: str, WithDecryption: bool = False):
                raise RuntimeError("SSM down")

        secrets_client = _FailingSecretsClient()
        ssm_client = _FailingSSMClient()
        session = _DummySession(secrets_client=secrets_client, ssm_client=ssm_client)
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
                payload = secrets_preflight.run_secrets_preflight(
                    env_name="dev",
                    region="us-east-2",
                    session=session,
                    fail_on_error=False,
                )
        self.assertEqual(payload["secrets"]["rp-mw/dev/openai/api_key"]["readable"], False)
        self.assertEqual(payload["ssm"]["/rp-mw/dev/safe_mode"]["error"], "RuntimeError")
        result = secrets_preflight._check_secret(
            _FailingSecretsClient(), "rp-mw/dev/openai/api_key", required=True
        )
        self.assertFalse(result.readable)

    def test_secrets_preflight_writes_output(self) -> None:
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
                with tempfile.TemporaryDirectory() as tmpdir:
                    out_path = os.path.join(tmpdir, "payload.json")
                    payload = secrets_preflight.run_secrets_preflight(
                        env_name="dev",
                        region="us-east-2",
                        session=session,
                        out_path=out_path,
                        fail_on_error=False,
                    )
                    self.assertTrue(os.path.exists(out_path))
        self.assertEqual(payload["overall_status"], "PASS")

    def test_secrets_preflight_fail_on_error(self) -> None:
        missing = {"rp-mw/dev/richpanel/api_key"}
        session = _DummySession(secrets_client=_DummySecretsClient(missing_ids=missing))
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
                with self.assertRaises(SystemExit):
                    secrets_preflight.run_secrets_preflight(
                        env_name="dev",
                        region="us-east-2",
                        session=session,
                        fail_on_error=True,
                    )

    def test_secrets_preflight_main(self) -> None:
        with patch.object(
            secrets_preflight,
            "run_secrets_preflight",
            return_value={"overall_status": "PASS"},
        ):
            with patch("sys.argv", ["secrets_preflight.py", "--env", "dev"]):
                self.assertEqual(secrets_preflight.main(), 0)


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

    def test_sync_bot_agent_secret_missing_env(self) -> None:
        secrets_client = _DummySecretsClient(missing_ids={"rp-mw/prod/richpanel/bot_agent_id"})
        lambda_client = _DummyLambdaClient(bot_agent_id=None)
        session = _DummySession(secrets_client=secrets_client, lambda_client=lambda_client)
        with patch.object(sync_bot_agent_secret, "boto3", new=SimpleNamespace(session=SimpleNamespace(Session=lambda region_name=None: session))):
            with self.assertRaises(SystemExit):
                sync_bot_agent_secret.main_with_args(env="prod", region="us-east-2")

    def test_sync_bot_agent_secret_boto3_missing(self) -> None:
        with patch.object(sync_bot_agent_secret, "boto3", new=None):
            with self.assertRaises(SystemExit):
                sync_bot_agent_secret.main_with_args(env="prod", region="us-east-2")

    def test_sync_bot_agent_secret_helpers(self) -> None:
        self.assertEqual(aws_account_preflight.normalize_env("production"), "prod")
        self.assertEqual(sync_bot_agent_secret._resolve_region(None), "us-east-2")

    def test_sync_bot_agent_secret_main(self) -> None:
        with patch.object(sync_bot_agent_secret, "main_with_args", return_value=0):
            with patch("sys.argv", ["sync_bot_agent_secret.py", "--env", "dev"]):
                self.assertEqual(sync_bot_agent_secret.main(), 0)


if __name__ == "__main__":
    raise SystemExit(unittest.main())
