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

    def test_preflight_boto3_unavailable(self) -> None:
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "payload.json")
            with mock.patch.object(aws_secrets_preflight, "boto3", new=None):
                payload = aws_secrets_preflight.run_aws_secrets_preflight(
                    env_name="dev",
                    region="us-east-2",
                    session=None,
                    out_path=out_path,
                    fail_on_error=False,
                )
            self.assertTrue(os.path.exists(out_path))
        self.assertEqual(payload["overall_status"], "FAIL")
        self.assertEqual(payload["error"], "boto3_unavailable")
        with mock.patch.object(aws_secrets_preflight, "boto3", new=None):
            with self.assertRaises(SystemExit):
                aws_secrets_preflight.run_aws_secrets_preflight(
                    env_name="dev",
                    region="us-east-2",
                    session=None,
                    fail_on_error=True,
                )

    def test_preflight_region_mismatch_message(self) -> None:
        session = _DummySession()
        account_result = aws_account_preflight.AccountPreflightResult(
            env="dev",
            region="us-west-1",
            aws_account_id="151124909266",
            aws_arn=None,
            expected_account_id="151124909266",
            expected_region="us-east-2",
            ok=False,
            error="region_mismatch(expected=us-east-2,actual=us-west-1)",
        )
        with mock.patch.object(aws_secrets_preflight, "boto3", new=SimpleNamespace()):
            with mock.patch.object(
                aws_secrets_preflight, "run_account_preflight", return_value=account_result
            ):
                with self.assertRaises(SystemExit) as ctx:
                    aws_secrets_preflight.run_aws_secrets_preflight(
                        env_name="dev",
                        region="us-west-1",
                        session=session,
                        fail_on_error=True,
                    )
        self.assertIn("wrong region", str(ctx.exception))

    def test_preflight_unknown_env_message(self) -> None:
        session = _DummySession()
        account_result = aws_account_preflight.AccountPreflightResult(
            env="unknown",
            region="us-east-2",
            aws_account_id=None,
            aws_arn=None,
            expected_account_id=None,
            expected_region="us-east-2",
            ok=False,
            error="unknown_env",
        )
        with mock.patch.object(aws_secrets_preflight, "boto3", new=SimpleNamespace()):
            with mock.patch.object(
                aws_secrets_preflight, "run_account_preflight", return_value=account_result
            ):
                with self.assertRaises(SystemExit) as ctx:
                    aws_secrets_preflight.run_aws_secrets_preflight(
                        env_name="unknown",
                        region="us-east-2",
                        session=session,
                        fail_on_error=True,
                    )
        self.assertIn("unknown env", str(ctx.exception))

    def test_preflight_writes_output_and_extra_secret(self) -> None:
        session = _DummySession()
        with mock.patch.object(aws_secrets_preflight, "boto3", new=SimpleNamespace()):
            with mock.patch.object(
                aws_secrets_preflight,
                "run_account_preflight",
                return_value=aws_account_preflight.AccountPreflightResult(
                    env="dev",
                    region="us-east-2",
                    aws_account_id="151124909266",
                    aws_arn=None,
                    expected_account_id="151124909266",
                    expected_region="us-east-2",
                    ok=True,
                    error=None,
                ),
            ):
                import tempfile
                import os

                with tempfile.TemporaryDirectory() as tmpdir:
                    out_path = os.path.join(tmpdir, "payload.json")
                    payload = aws_secrets_preflight.run_aws_secrets_preflight(
                        env_name="dev",
                        region="us-east-2",
                        session=session,
                        require_secrets=["rp-mw/dev/shopify/custom_extra"],
                        out_path=out_path,
                        fail_on_error=False,
                    )
                    self.assertTrue(os.path.exists(out_path))
        self.assertIn("rp-mw/dev/shopify/custom_extra", payload["secrets"])

    def test_preflight_fail_on_error_includes_secret_detail(self) -> None:
        missing = {"rp-mw/dev/shopify/admin_api_token"}
        secrets_client = _DummySecretsClient(missing_ids=missing)
        session = _DummySession(secrets_client=secrets_client)
        with mock.patch.object(aws_secrets_preflight, "boto3", new=SimpleNamespace()):
            with mock.patch.object(
                aws_secrets_preflight,
                "run_account_preflight",
                return_value=aws_account_preflight.AccountPreflightResult(
                    env="dev",
                    region="us-east-2",
                    aws_account_id="151124909266",
                    aws_arn=None,
                    expected_account_id="151124909266",
                    expected_region="us-east-2",
                    ok=True,
                    error=None,
                ),
            ):
                with self.assertRaises(SystemExit) as ctx:
                    aws_secrets_preflight.run_aws_secrets_preflight(
                        env_name="dev",
                        region="us-east-2",
                        session=session,
                        fail_on_error=True,
                    )
        message = str(ctx.exception)
        self.assertIn("secret_id: rp-mw/dev/shopify/admin_api_token", message)

    def test_main_exit_code(self) -> None:
        with mock.patch.object(
            aws_secrets_preflight,
            "run_aws_secrets_preflight",
            return_value={"overall_status": "PASS"},
        ):
            with mock.patch("sys.argv", ["aws_secrets_preflight.py", "--env", "dev"]):
                self.assertEqual(aws_secrets_preflight.main(), 0)


def main() -> int:  # pragma: no cover
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AwsSecretsPreflightTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
