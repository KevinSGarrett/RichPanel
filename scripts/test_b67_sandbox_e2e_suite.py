import unittest
from pathlib import Path

from b67_sandbox_e2e_suite import (
    ScenarioSpec,
    _append_scenario_assertions,
    _build_scenario_spec,
    _build_smoke_cmd,
    _extract_ticket_ref,
    _redact_command,
    _run_scenario,
    _suite_results_json,
)


class _Args:
    def __init__(self) -> None:
        self.scenario = "order_status_fallback_email_match"
        self.order_number = None
        self.env = "dev"
        self.region = "us-east-2"
        self.stack_name = "RichpanelMiddleware-dev"
        self.profile = None
        self.allowlist_email = None
        self.followup_message = "ok"
        self.wait_seconds = None
        self.ticket_number = None
        self.ticket_id = None
        self.suite = False


class TestB67SandboxSuite(unittest.TestCase):
    def test_build_scenario_spec_fallback_has_no_order_number(self) -> None:
        args = _Args()
        scenario = _build_scenario_spec(args, run_id="TEST")
        self.assertEqual(scenario.scenario_key, "order_status_fallback_email_match")
        self.assertIsNone(scenario.order_number)
        self.assertFalse(scenario.require_order_match_by_number)

    def test_append_scenario_assertions_fallback_passes(self) -> None:
        proof = {
            "proof_fields": {
                "intent_after": "order_status_tracking",
                "outbound_attempted": True,
                "order_match_success": True,
                "order_match_method": "email_only",
                "send_message_path_confirmed": True,
                "operator_reply_confirmed": True,
            },
            "richpanel": {"status_after": "CLOSED"},
        }
        scenario = ScenarioSpec(
            scenario_key="order_status_fallback_email_match",
            smoke_scenario="order_status",
            ticket_subject="",
            ticket_body="",
            proof_filename="x.json",
            require_openai_routing=True,
            require_openai_rewrite=True,
            require_outbound=True,
            require_send_message=True,
            require_operator_reply=True,
            followup=False,
        )
        status, failure = _append_scenario_assertions(proof, scenario=scenario)
        self.assertEqual(status, "PASS")
        self.assertIsNone(failure)

    def test_suite_results_json_includes_env_flags(self) -> None:
        results = []
        payload = _suite_results_json(results, run_id="RUN123", env_flags={"X": "Y"})
        self.assertEqual(payload["run_id"], "RUN123")
        self.assertEqual(payload["environment"], "sandbox")
        self.assertEqual(payload["env_flags"]["X"], "Y")

    def test_redact_command_masks_sensitive_flags(self) -> None:
        cmd = [
            "python",
            "scripts/dev_e2e_smoke.py",
            "--ticket-number",
            "12345",
            "--allowlist-email=test@example.com",
            "--region",
            "us-east-2",
        ]
        redacted = _redact_command(cmd)
        self.assertIn("--ticket-number <redacted>", redacted)
        self.assertIn("--allowlist-email=<redacted>", redacted)
        self.assertIn("--region us-east-2", redacted)

    def test_extract_ticket_ref_parses_payload(self) -> None:
        output = "\n".join(
            [
                "INFO: created",
                "TICKET_REF_JSON:{\"ticket_number\":\"123\",\"ticket_id\":\"abc\"}",
            ]
        )
        ref = _extract_ticket_ref(output)
        self.assertEqual(ref["ticket_number"], "123")
        self.assertEqual(ref["ticket_id"], "abc")

    def test_extract_ticket_ref_raises_without_marker(self) -> None:
        with self.assertRaises(RuntimeError):
            _extract_ticket_ref("no marker here")

    def test_build_smoke_cmd_includes_flags(self) -> None:
        args = _Args()
        scenario = ScenarioSpec(
            scenario_key="order_status_golden",
            smoke_scenario="order_status",
            ticket_subject="",
            ticket_body="",
            proof_filename="x.json",
            require_openai_routing=True,
            require_openai_rewrite=False,
            require_order_match_by_number=True,
            require_outbound=True,
            require_send_message=True,
            require_operator_reply=True,
            followup=True,
            order_number="1001",
        )
        cmd = _build_smoke_cmd(
            args,
            scenario=scenario,
            proof_path=Path("proof.json"),
            run_id="RUN",
            ticket_number="555",
            ticket_id=None,
        )
        self.assertIn("--require-openai-routing", cmd)
        self.assertIn("--no-require-openai-rewrite", cmd)
        self.assertIn("--require-order-match-by-number", cmd)
        self.assertIn("--followup", cmd)
        self.assertIn("--ticket-number", cmd)
        self.assertIn("555", cmd)

    def test_run_scenario_blocks_ticket_with_suite(self) -> None:
        args = _Args()
        args.suite = True
        args.ticket_number = "123"
        scenario = ScenarioSpec(
            scenario_key="order_status_golden",
            smoke_scenario="order_status",
            ticket_subject="",
            ticket_body="",
            proof_filename="x.json",
        )
        result = _run_scenario(
            args,
            scenario=scenario,
            run_id="RUN",
            artifacts_dir=Path("."),
        )
        self.assertEqual(result.status, "ERROR")


if __name__ == "__main__":
    unittest.main()
