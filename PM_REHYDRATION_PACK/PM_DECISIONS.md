# PM Decisions

Date: 2025-12-30

## Decision log (most recent first)

### 2025-12-30 — Enter Build Mode (B00)
- **Decision:** We are ready to switch from Foundation Mode to **Build Mode** with Cursor agents doing day-to-day work.
- **Why:** CI is stable and deterministic; GitHub protections are in place; the repo contains the required docs/policies/runbooks.

### 2025-12-30 — GitHub merge strategy is merge-commit only
- **Decision:** Keep `allow_merge_commit=true` and disable squash + rebase merges.
- **Why:** Predictable history and easiest multi-agent conflict resolution.

### 2025-12-30 — Main branch protection rules
- **Required status check:** `validate` (strict/up-to-date required)
- **Admin enforcement:** on
- **PR reviews:** enabled with `required_approving_review_count=0` (PR required; approvals not required)
- **Conversation resolution:** on
- **Force pushes/deletions:** disabled

### 2025-12-30 — Deterministic regen outputs
- **Doc registry:** canonical POSIX path sort key
- **Reference registry:** canonical POSIX path sort key + newline-normalized `size_bytes`
- **Plan checklist:** stable banner (no date stamping)
- **Motivation:** avoid CI thrash from ordering/timestamps/line ending differences.

### 2025-12-29 — Change Request CR-001 integrated
- No tracking numbers; delivery estimate only.
- Defer discovery work that assumes tracking visibility.
