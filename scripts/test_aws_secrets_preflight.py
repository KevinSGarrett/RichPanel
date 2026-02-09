import unittest
from types import SimpleNamespace
from unittest import mock

import aws_account_preflight
import aws_secrets_preflight


class _DummySecretsClient:
    def __init__(self, *, missing_ids=None, unreadable_ids=None) -> None:
        self._missing = set(missing_ids or [])
        self._unreadable = set(unreadable_ids or [])

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


class _DummySTSClient:
    def __init__(self, account_id: str) -> None:
        self._account_id = account_id

    def get_caller_identity(self):
        return {"Account": self._account_id, "Arn": "arn:aws:sts::123:role/demo"}


class _DummySession:
    def __init__(self, *, account_id: str = "151124909266", secrets_client=None) -> None:
        self._account_id = account_id
        self._secrets = secrets_client or _DummySecretsClient()

    def client(self, service_name: str, region_name=None):
        if service_name == "secretsmanager":
            return self._secrets
        if service_name == "sts":
            return _DummySTSClient(self._account_id)
        raise ValueError(f"Unexpected service: {service_name}")


class AwsSecretsPreflightTests(unittest.TestCase):
    def test_required_secret_ids(self) -> None:
        required = aws_secrets_preflight._required_secret_ids("dev")
        self.assertIn("rp-mw/dev/shopify/admin_api_token", required)
        self.assertIn("rp-mw/dev/shopify/client_id", required)
        self.assertIn("rp-mw/dev/shopify/client_secret", required)
        self.assertIn("rp-mw/dev/shopify/refresh_token", required)

    def test_preflight_success(self) -> None:
        session = _DummySession()
        with mock.patch.object(aws_secrets_preflight, "boto3", new=SimpleNamespace()):
            with mock.patch.object(
                aws_secrets_preflight,
                "run_account_preflight",
                return_value=aws_account_preflight.AccountPreflightResult(
                    env="dev",
                    region="us-east-2",
                    aws_account_id="151124909266",
                    aws_arn="arn:aws:sts::151124909266:role/demo",
                    expected_account_id="151124909266",
                    expected_region="us-east-2",
                    ok=True,
                    error=None,
                ),
            ):
                payload = aws_secrets_preflight.run_aws_secrets_preflight(
                    env_name="dev",
                    region="us-east-2",
                    session=session,
                    fail_on_error=False,
                )
        self.assertEqual(payload["overall_status"], "PASS")
        self.assertIn("rp-mw/dev/shopify/admin_api_token", payload["secrets"])

    def test_preflight_account_mismatch_fails(self) -> None:
        session = _DummySession(account_id="000000000000")
        account_result = aws_account_preflight.AccountPreflightResult(
            env="dev",
            region="us-east-2",
            aws_account_id="000000000000",
            aws_arn=None,
            expected_account_id="151124909266",
            expected_region="us-east-2",
            ok=False,
            error="account_mismatch",
        )
        with mock.patch.object(aws_secrets_preflight, "boto3", new=SimpleNamespace()):
            with mock.patch.object(
                aws_secrets_preflight, "run_account_preflight", return_value=account_result
            ):
                with self.assertRaises(SystemExit) as ctx:
                    aws_secrets_preflight.run_aws_secrets_preflight(
                        env_name="dev",
                        region="us-east-2",
                        session=session,
                        fail_on_error=True,
                    )
        self.assertIn("wrong account", str(ctx.exception))


def main() -> int:  # pragma: no cover
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AwsSecretsPreflightTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
