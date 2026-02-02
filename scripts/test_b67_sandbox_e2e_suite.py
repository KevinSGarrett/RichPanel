import unittest

from b67_sandbox_e2e_suite import (
    ScenarioSpec,
    _append_scenario_assertions,
    _build_scenario_spec,
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


if __name__ == "__main__":
    unittest.main()
