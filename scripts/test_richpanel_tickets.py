from __future__ import annotations

import json
import unittest
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from richpanel_middleware.integrations.richpanel.client import RichpanelResponse
from richpanel_middleware.integrations.richpanel.tickets import (
    TicketMetadata,
    dedupe_tags,
    get_ticket_metadata,
)


class _ExecWithMethod:
    def __init__(self) -> None:
        self.calls = 0

    def get_ticket_metadata(self, conversation_id: str, dry_run: bool):  # type: ignore[no-untyped-def]
        self.calls += 1
        class _Upstream:
            def __init__(self) -> None:
                self.status = " open "
                self.tags = ["tag1", "tag1", "tag2"]
                self.status_code = 200
                self.dry_run = dry_run

        return _Upstream()


class _ExecWithHttp:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.calls = 0

    def execute(self, method: str, path: str, *, dry_run: bool):  # type: ignore[no-untyped-def]
        self.calls += 1
        return RichpanelResponse(
            status_code=200,
            headers={},
            body=json.dumps(self.payload).encode("utf-8"),
            url=path,
            dry_run=dry_run,
        )


class TicketsTests(unittest.TestCase):
    def test_dedupe_tags_strips_blank_and_dupes(self) -> None:
        tags = dedupe_tags([" a ", " ", "b", "a"])
        self.assertEqual(tags, {"a", "b"})

    def test_get_ticket_metadata_via_executor_method(self) -> None:
        exec_method = _ExecWithMethod()
        metadata = get_ticket_metadata("t-1", exec_method, allow_network=False)

        self.assertEqual(metadata.status, "open")
        self.assertEqual(metadata.tags, {"tag1", "tag2"})
        self.assertTrue(metadata.dry_run)
        self.assertEqual(exec_method.calls, 1)

    def test_get_ticket_metadata_via_http_execute(self) -> None:
        payload = {"status": "open", "tags": ["mw-auto", "mw-auto", "route"]}
        exec_http = _ExecWithHttp(payload)

        metadata = get_ticket_metadata("t-2", exec_http, allow_network=True)

        self.assertEqual(metadata.status, "open")
        self.assertEqual(metadata.tags, {"mw-auto", "route"})
        self.assertFalse(metadata.dry_run)
        self.assertEqual(metadata.status_code, 200)
        self.assertEqual(exec_http.calls, 1)


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TicketsTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())

