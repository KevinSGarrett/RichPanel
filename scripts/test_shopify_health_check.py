import json
import tempfile
from pathlib import Path
import unittest

import shopify_health_check as health_check


class _StubClient:
    def __init__(self, client_id, client_secret):
        self._client_id = client_id
        self._client_secret = client_secret

    def _load_client_credentials(self):
        return self._client_id, self._client_secret


class ShopifyHealthCheckTests(unittest.TestCase):
    def test_safe_token_format(self) -> None:
        self.assertEqual(health_check._safe_token_format(None), "unknown")
        self.assertEqual(health_check._safe_token_format("json"), "json")
        self.assertEqual(health_check._safe_token_format("plain"), "raw")

    def test_load_client_credentials(self) -> None:
        client = _StubClient("id", "secret")
        has_id, has_secret = health_check._load_client_credentials(client)
        self.assertTrue(has_id)
        self.assertTrue(has_secret)

        client = _StubClient(None, None)
        has_id, has_secret = health_check._load_client_credentials(client)
        self.assertFalse(has_id)
        self.assertFalse(has_secret)

    def test_write_json(self) -> None:
        payload = {"b": 2, "a": 1}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.json"
            health_check._write_json(path, payload)
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data, payload)


if __name__ == "__main__":
    unittest.main()
