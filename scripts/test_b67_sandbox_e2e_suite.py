import tempfile
import unittest
from pathlib import Path
from unittest import mock

from b67_sandbox_e2e_suite import (
    ScenarioSpec,
    ScenarioRunResult,
    _append_scenario_assertions,
    _build_scenario_spec,
    _build_smoke_cmd,
    _extract_ticket_ref,
    _redact_command,
    _run_scenario,
    _suite_summary_md,
    _suite_results_json,
    main,
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

    def test_build_scenario_spec_golden_normalizes_order_number(self) -> None:
        args = _Args()
        args.scenario = "order_status_golden"
        args.order_number = "#1002"
        scenario = _build_scenario_spec(args, run_id="RUN")
        self.assertEqual(scenario.order_number, "1002")
        self.assertTrue(scenario.require_order_match_by_number)
        self.assertIsNotNone(scenario.order_number_fingerprint)

    def test_build_scenario_spec_negative_case(self) -> None:
        args = _Args()
        args.scenario = "not_order_status_negative_case"
        scenario = _build_scenario_spec(args, run_id="RUN")
        self.assertEqual(scenario.scenario_key, "not_order_status_negative_case")
        self.assertFalse(scenario.require_send_message)

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

    def test_append_scenario_assertions_negative_case_passes(self) -> None:
        proof = {
            "proof_fields": {
                "intent_after": "returns",
                "outbound_attempted": False,
                "routed_to_support": True,
            },
            "richpanel": {"status_after": "OPEN"},
        }
        scenario = ScenarioSpec(
            scenario_key="not_order_status_negative_case",
            smoke_scenario="not_order_status",
            ticket_subject="",
            ticket_body="",
            proof_filename="x.json",
            require_openai_routing=True,
            require_openai_rewrite=False,
        )
        status, failure = _append_scenario_assertions(proof, scenario=scenario)
        self.assertEqual(status, "PASS")
        self.assertIsNone(failure)

    def test_append_scenario_assertions_followup_passes(self) -> None:
        proof = {
            "proof_fields": {
                "intent_after": "order_status_tracking",
                "outbound_attempted": True,
                "send_message_path_confirmed": True,
                "operator_reply_confirmed": True,
                "followup_reply_sent": False,
                "followup_routed_support": True,
            },
            "richpanel": {"status_after": "CLOSED"},
        }
        scenario = ScenarioSpec(
            scenario_key="followup_after_autoclose",
            smoke_scenario="order_status",
            ticket_subject="",
            ticket_body="",
            proof_filename="x.json",
            require_openai_routing=True,
            require_openai_rewrite=True,
            require_outbound=True,
            require_send_message=True,
            require_operator_reply=True,
            followup=True,
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

    def test_run_scenario_handles_successful_flow(self) -> None:
        args = _Args()
        scenario = ScenarioSpec(
            scenario_key="order_status_golden",
            smoke_scenario="order_status",
            ticket_subject="",
            ticket_body="",
            proof_filename="proof.json",
            require_outbound=True,
            require_send_message=True,
            require_operator_reply=True,
        )
        proof = {
            "proof_fields": {
                "intent_after": "order_status_tracking",
                "outbound_attempted": True,
                "send_message_path_confirmed": True,
                "operator_reply_confirmed": True,
            },
            "richpanel": {"status_after": "CLOSED"},
        }
        create_stdout = "TICKET_REF_JSON:{\"ticket_number\":\"555\"}"
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            (artifacts / "PROOF").mkdir(parents=True, exist_ok=True)
            with mock.patch(
                "b67_sandbox_e2e_suite._run_command"
            ) as run_cmd, mock.patch(
                "b67_sandbox_e2e_suite._read_proof", return_value=proof
            ):
                run_cmd.side_effect = [
                    mock.Mock(returncode=0, stdout=create_stdout),
                    mock.Mock(returncode=0, stdout=""),
                ]
                result = _run_scenario(
                    args, scenario=scenario, run_id="RUN", artifacts_dir=artifacts
                )
        self.assertEqual(result.status, "PASS")

    def test_run_scenario_fails_without_ticket_ref(self) -> None:
        args = _Args()
        scenario = ScenarioSpec(
            scenario_key="order_status_golden",
            smoke_scenario="order_status",
            ticket_subject="",
            ticket_body="",
            proof_filename="proof.json",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            with mock.patch("b67_sandbox_e2e_suite._run_command") as run_cmd:
                run_cmd.return_value = mock.Mock(returncode=1, stdout="")
                result = _run_scenario(
                    args, scenario=scenario, run_id="RUN", artifacts_dir=artifacts
                )
        self.assertEqual(result.status, "FAIL")

    def test_run_scenario_smoke_failure_sets_error(self) -> None:
        args = _Args()
        scenario = ScenarioSpec(
            scenario_key="order_status_golden",
            smoke_scenario="order_status",
            ticket_subject="",
            ticket_body="",
            proof_filename="proof.json",
        )
        create_stdout = "TICKET_REF_JSON:{\"ticket_number\":\"555\"}"
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            (artifacts / "PROOF").mkdir(parents=True, exist_ok=True)
            with mock.patch(
                "b67_sandbox_e2e_suite._run_command"
            ) as run_cmd, mock.patch(
                "b67_sandbox_e2e_suite._read_proof", return_value=None
            ):
                run_cmd.side_effect = [
                    mock.Mock(returncode=0, stdout=create_stdout),
                    mock.Mock(returncode=2, stdout=""),
                ]
                result = _run_scenario(
                    args, scenario=scenario, run_id="RUN", artifacts_dir=artifacts
                )
        self.assertEqual(result.status, "FAIL")
        self.assertIsNotNone(result.error)

    def test_suite_summary_md_redacts_commands(self) -> None:
        result = ScenarioRunResult(
            scenario_key="order_status_golden",
            proof_path=Path("proof.json"),
            status="PASS",
            error=None,
            proof=None,
            commands=[["python", "x.py", "--ticket-number", "123"]],
        )
        summary = _suite_summary_md([result], run_id="RUN")
        self.assertIn("--ticket-number <redacted>", summary)

    def test_main_writes_suite_results_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            results_path = artifacts / "proof" / "suite_results.json"
            summary_path = artifacts / "proof" / "suite_summary.md"
            args = type(
                "Args",
                (),
                {
                    "scenario": None,
                    "suite": True,
                    "order_number": None,
                    "env": "dev",
                    "region": "us-east-2",
                    "stack_name": "stack",
                    "profile": None,
                    "allowlist_email": None,
                    "followup_message": "ok",
                    "wait_seconds": None,
                    "ticket_number": None,
                    "ticket_id": None,
                    "run_id": "RUN",
                    "artifacts_dir": str(artifacts),
                    "suite_results_path": str(results_path),
                    "suite_summary_path": str(summary_path),
                },
            )()
            result = ScenarioRunResult(
                scenario_key="order_status_golden",
                proof_path=artifacts / "proof.json",
                status="PASS",
                error=None,
                proof=None,
                commands=[],
            )
            with mock.patch("b67_sandbox_e2e_suite.parse_args", return_value=args), mock.patch(
                "b67_sandbox_e2e_suite._run_scenario", return_value=result
            ), mock.patch(
                "b67_sandbox_e2e_suite._capture_env_flags", return_value={}
            ):
                exit_code = main()
            self.assertEqual(exit_code, 0)
            self.assertTrue(results_path.exists())
            self.assertTrue(summary_path.exists())

    def test_main_returns_nonzero_on_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            results_path = artifacts / "proof" / "suite_results.json"
            summary_path = artifacts / "proof" / "suite_summary.md"
            args = type(
                "Args",
                (),
                {
                    "scenario": "order_status_golden",
                    "suite": False,
                    "order_number": None,
                    "env": "dev",
                    "region": "us-east-2",
                    "stack_name": "stack",
                    "profile": None,
                    "allowlist_email": None,
                    "followup_message": "ok",
                    "wait_seconds": None,
                    "ticket_number": None,
                    "ticket_id": None,
                    "run_id": "RUN",
                    "artifacts_dir": str(artifacts),
                    "suite_results_path": str(results_path),
                    "suite_summary_path": str(summary_path),
                },
            )()
            result = ScenarioRunResult(
                scenario_key="order_status_golden",
                proof_path=artifacts / "proof.json",
                status="FAIL",
                error="boom",
                proof=None,
                commands=[],
            )
            with mock.patch("b67_sandbox_e2e_suite.parse_args", return_value=args), mock.patch(
                "b67_sandbox_e2e_suite._run_scenario", return_value=result
            ), mock.patch(
                "b67_sandbox_e2e_suite._capture_env_flags", return_value={}
            ):
                exit_code = main()
        self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()
