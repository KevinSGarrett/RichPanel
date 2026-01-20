from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import live_readonly_shadow_eval as shadow_eval  # noqa: E402


class LiveReadonlyShadowEvalGuardTests(unittest.TestCase):
    def test_prod_requires_write_disabled(self) -> None:
        env = {
            "MW_ENV": "prod",
            "MW_ALLOW_NETWORK_READS": "true",
            "RICHPANEL_OUTBOUND_ENABLED": "true",
            "RICHPANEL_WRITE_DISABLED": "false",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            argv = ["live_readonly_shadow_eval.py", "--ticket-id", "123"]
            with mock.patch.object(sys, "argv", argv):
                with self.assertRaises(SystemExit) as ctx:
                    shadow_eval.main()
        self.assertIn("RICHPANEL_WRITE_DISABLED", str(ctx.exception))


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        LiveReadonlyShadowEvalGuardTests
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
