# Fix Report (If Applicable)

**Run ID:** RUN_20260116_1443Z  
**Agent:** C  
**Date:** 2026-01-16

## Failure observed
- error: Ticket close payload ambiguous; 2xx responses did not reliably close dev tickets.
- where: order_status pipeline (Richpanel updates) and dev environment tickets.
- repro steps: order_status runs returned 2xx but ticket remained OPEN; no consistent close payload identified.

## Diagnosis
- likely root cause: Pipeline stopped on first 2xx without post-read confirmation; close payload ordering missing working combination for dev (`ticket.state=closed` + `status=CLOSED`).

## Fix applied
- files changed: `scripts/dev_richpanel_close_probe.py`, `backend/src/richpanel_middleware/automation/pipeline.py`, `backend/src/richpanel_middleware/integrations/richpanel/tickets.py`, `scripts/test_pipeline_handlers.py`.
- why it works: Probe identified winning payload; pipeline now tries it first and requires post-read status change/closed state before succeeding; tests ensure we continue past 2xx-without-close.

## Verification
- tests run: `python scripts/dev_richpanel_close_probe.py ...`, `python scripts/dev_e2e_smoke.py ...`, `python scripts/run_ci_checks.py --ci`
- results: Probe PASS (winning payload `ticket_state_closed_status_CLOSED`); E2E PASS_WEAK (ticket already closed); CI-equivalent pass.
