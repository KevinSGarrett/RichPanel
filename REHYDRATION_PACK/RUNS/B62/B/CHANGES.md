# B62/B Changes

## Code

- Added channel detection helpers to prefer envelope/ticket metadata and standardize channel selection.
- Enforced email-only `/send-message` usage with operator-comment verification before closing tickets.
- Applied allowlist gating across outbound paths to fail closed when blocked.
- Added caching for bot author ID resolution to avoid repeated `/v1/users` calls.
- Added a send-message operator-missing tag for deterministic failure routing.

## Tests

- Added/updated outbound tests for non-email routing, allowlist blocking, operator verification, and author cache.

## Docs / Artifacts

- Added `docs/08_Engineering/Richpanel_Reply_Paths.md`.
- Added `scripts/create_sandbox_chat_ticket.py` to attempt non-email ticket creation for proofs.
- Added `REHYDRATION_PACK/RUNS/B62/B/PROOF/*` artifacts for unit tests and dev smoke proof.
