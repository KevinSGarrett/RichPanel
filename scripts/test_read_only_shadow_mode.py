from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from richpanel_middleware.automation import pipeline  # noqa: E402
from richpanel_middleware.automation.router import RoutingDecision  # noqa: E402


class _RoutingArtifact:
    def __init__(self, primary_source: str = "deterministic") -> None:
        self.primary_source = primary_source

    def to_dict(self) -> dict:
        return {"primary_source": self.primary_source}


class ReadOnlyShadowModeTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ.pop("RICHPANEL_OUTBOUND_ENABLED", None)
        os.environ.pop("MW_ALLOW_NETWORK_READS", None)

    def test_plan_actions_propagates_allow_network_for_shadow_reads(self) -> None:
        envelope = SimpleNamespace(
            event_id="evt-shadow-1",
            conversation_id="c-shadow-1",
            payload={"customer_message": "where is my order?"},
            received_at="2024-01-01T00:00:00Z",
        )
        routing = RoutingDecision(
            category="order_status",
            tags=["mw-routing-applied"],
            reason="stubbed",
            department="Email Support Team",
            intent="order_status_tracking",
        )
        artifact = _RoutingArtifact()

        with mock.patch.object(
            pipeline, "compute_dual_routing", return_value=(routing, artifact)
        ), mock.patch.object(
            pipeline,
            "lookup_order_summary",
            return_value={
                "order_id": "123",
                "created_at": "2024-01-01T00:00:00Z",
                "shipping_method": "2 business days",
            },
        ) as lookup_mock:
            plan = pipeline.plan_actions(
                envelope,
                safe_mode=False,
                automation_enabled=True,
                allow_network=True,
                outbound_enabled=False,
            )

        lookup_mock.assert_called_once()
        self.assertTrue(lookup_mock.call_args.kwargs.get("allow_network"))
        self.assertIsNotNone(plan)
        self.assertTrue(any(action.get("type") == "order_status_draft_reply" for action in plan.actions))

    def test_outbound_disabled_skips_writes_while_allowing_shadow_reads(self) -> None:
        plan = pipeline.ActionPlan(
            event_id="evt-shadow-2",
            mode="automation_candidate",
            safe_mode=False,
            automation_enabled=True,
            actions=[
                {
                    "type": "order_status_draft_reply",
                    "conversation_id": "c-shadow-2",
                    "parameters": {"draft_reply": {"body": "hello"}},
                    "reasons": [],
                }
            ],
            reasons=[],
            routing=RoutingDecision(
                category="order_status",
                tags=["mw-routing-applied"],
                reason="stubbed",
                department="Email Support Team",
                intent="order_status_tracking",
            ),
            routing_artifact=None,
        )
        envelope = SimpleNamespace(
            event_id="evt-shadow-2",
            conversation_id="c-shadow-2",
            payload={},
            received_at="2024-01-01T00:00:00Z",
        )
        mock_executor = mock.Mock()
        rewrite_result = SimpleNamespace(
            rewritten=False,
            body=None,
            reason="skipped",
            confidence=0.0,
            dry_run=True,
            model="test",
            risk_flags=[],
            fingerprint="fp",
        )

        with mock.patch.object(pipeline, "_resolve_target_ticket_id", return_value="c-shadow-2"), mock.patch.object(
            pipeline, "_safe_ticket_metadata_fetch", return_value=SimpleNamespace(status=None, tags=[])
        ), mock.patch.object(
            pipeline, "rewrite_reply", return_value=rewrite_result
        ):
            result = pipeline.execute_order_status_reply(
                envelope,
                plan,
                safe_mode=False,
                automation_enabled=True,
                allow_network=True,
                outbound_enabled=False,
                richpanel_executor=mock_executor,
            )

        self.assertFalse(result.get("sent"))
        mock_executor.execute.assert_not_called()

        mock_executor.reset_mock()
        with mock.patch.object(pipeline, "_resolve_target_ticket_id", return_value="c-shadow-2"):
            routing_result = pipeline.execute_routing_tags(
                envelope,
                plan,
                safe_mode=False,
                automation_enabled=True,
                allow_network=True,
                outbound_enabled=False,
                richpanel_executor=mock_executor,
            )

        self.assertFalse(routing_result.get("applied"))
        mock_executor.execute.assert_not_called()


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ReadOnlyShadowModeTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())

