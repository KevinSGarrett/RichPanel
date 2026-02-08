import io
import runpy
import unittest
from unittest import mock

import shopify_token_health_check as token_check


class ShopifyTokenHealthCheckWrapperTests(unittest.TestCase):
    def test_main_prints_account_and_delegates(self) -> None:
        with mock.patch.object(
            token_check, "_load_aws_account_id", return_value="123456789012"
        ):
            with mock.patch("shopify_health_check.main", return_value=0) as stub_main:
                with mock.patch("sys.stdout", new_callable=io.StringIO) as handle:
                    exit_code = token_check.main()
        output = handle.getvalue().strip().splitlines()
        self.assertTrue(output)
        self.assertEqual(output[0], "Account=123456789012")
        self.assertEqual(exit_code, 0)
        stub_main.assert_called_once()

    def test_module_main_guard(self) -> None:
        with mock.patch("shopify_health_check._load_aws_account_id", return_value=None):
            with mock.patch("shopify_health_check.main", return_value=0):
                with mock.patch("sys.stdout", new_callable=io.StringIO):
                    with self.assertRaises(SystemExit) as ctx:
                        runpy.run_module(
                            "shopify_token_health_check", run_name="__main__"
                        )
        self.assertEqual(ctx.exception.code, 0)


def main() -> int:  # pragma: no cover
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        ShopifyTokenHealthCheckWrapperTests
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
