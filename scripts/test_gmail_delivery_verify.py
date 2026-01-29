from __future__ import annotations

import unittest

from gmail_delivery_verify import (
    _fingerprint,
    _parse_internal_date,
    _redact_query,
    _sanitize_message_entry,
    _build_proof_payload,
    _normalize_query,
)


class GmailVerifyHelperTests(unittest.TestCase):
    def test_fingerprint_handles_none(self) -> None:
        self.assertIsNone(_fingerprint(None))

    def test_redact_query_masks_emails(self) -> None:
        query = "to:(user+test@example.com) subject:(Order Status)"
        redacted = _redact_query(query)
        self.assertNotIn("example.com", redacted)
        self.assertIn("<redacted>", redacted)

    def test_parse_internal_date(self) -> None:
        self.assertIsNone(_parse_internal_date("bad"))
        self.assertIsNotNone(_parse_internal_date("1700000000000"))

    def test_sanitize_message_entry_hashes_headers(self) -> None:
        entry = _sanitize_message_entry(
            {
                "id": "msg-1",
                "threadId": "thread-1",
                "internalDate": "1700000000000",
                "labelIds": ["INBOX"],
                "headers": [
                    {"name": "Subject", "value": "Order Status"},
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "To", "value": "receiver@example.com"},
                    {"name": "Delivered-To", "value": "receiver@example.com"},
                    {"name": "X-Original-To", "value": "alias@example.com"},
                    {"name": "Date", "value": "Mon, 01 Jan 2026 00:00:00 +0000"},
                ],
            },
            expected_to="receiver@example.com",
        )
        self.assertIn("id_fingerprint", entry)
        self.assertIn("subject_hash", entry)
        self.assertIsNone(entry.get("subject"))
        self.assertEqual(entry.get("label_ids"), ["INBOX"])
        self.assertTrue(entry.get("matches_expected_to"))
        self.assertIsNotNone(entry.get("delivered_to_hash"))
        self.assertIsNotNone(entry.get("original_to_hash"))

    def test_build_proof_payload_no_messages(self) -> None:
        payload = _build_proof_payload(
            query="to:(user@example.com)",
            user="me",
            messages=[],
            max_results=5,
            expected_to=None,
            profile_email=None,
        )
        self.assertEqual(payload["result"]["status"], "not_found")
        self.assertEqual(payload["result"]["message_count"], 0)

    def test_build_proof_payload_with_messages(self) -> None:
        payload = _build_proof_payload(
            query="to:(user@example.com)",
            user="me",
            messages=[
                {
                    "id": "msg-2",
                    "threadId": "thread-2",
                    "internalDate": "1700000000000",
                    "labelIds": ["INBOX"],
                    "headers": [
                        {"name": "Subject", "value": "Order Status"},
                    ],
                }
            ],
            max_results=5,
            expected_to="user@example.com",
            profile_email=None,
        )
        self.assertEqual(payload["result"]["status"], "not_found")
        self.assertEqual(payload["result"]["message_count"], 1)
        self.assertTrue(payload["messages"][0]["id_fingerprint"])
        self.assertEqual(payload["result"]["expected_to_match_count"], 0)

        payload_match = _build_proof_payload(
            query="to:(user@example.com)",
            user="me",
            messages=[
                {
                    "id": "msg-3",
                    "threadId": "thread-3",
                    "internalDate": "1700000000000",
                    "labelIds": ["INBOX"],
                    "headers": [
                        {"name": "Subject", "value": "Order Status"},
                        {"name": "To", "value": "User <user@example.com>"},
                    ],
                }
            ],
            max_results=5,
            expected_to="user@example.com",
            profile_email="user@example.com",
        )
        self.assertEqual(payload_match["result"]["status"], "found")
        self.assertEqual(payload_match["result"]["expected_to_match_count"], 1)
        self.assertTrue(payload_match["meta"]["profile_email_hash"])

    def test_normalize_query(self) -> None:
        query = _normalize_query(["subject:(Order", "Status)", "to:(user@example.com)"])
        self.assertEqual(query, "subject:(Order Status) to:(user@example.com)")


if __name__ == "__main__":
    unittest.main()
