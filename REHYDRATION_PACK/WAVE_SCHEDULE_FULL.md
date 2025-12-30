# Wave Schedule (Full)

Last updated: 2025-12-29 — Current wave: **WAVE_B00 (Build kickoff + Cursor agent takeover)**

This file documents what each wave contains and what “done” means.

## Notes
- Foundation waves (Fxx) establish the repo “OS”: docs, policies, runbooks, validators, registries, and reference material.
- Build waves (Bxx) are implementation sprints where Cursor agents create code and RUN artifacts.
- All work is expected to flow through PRs (no direct pushes to `main`).

---

# Build Mode Waves

## WAVE_B00 — Build kickoff + Cursor agent takeover
**Objective:** Switch the repo to Build Mode and formalize Cursor-agent ownership of day-to-day GitOps.

**Entry criteria:**
- CI green on `main`
- Branch protection enabled on `main` with required check `validate` (strict), enforce admins, and no force pushes
- Deterministic regen scripts (doc/reference registries, plan checklist)

**Deliverables:**
- `REHYDRATION_PACK/MODE.yaml` set to `mode: build`
- Updated rehydration + PM packs reflecting the current GitHub/CI configuration
- `REHYDRATION_PACK/06_AGENT_ASSIGNMENTS.md` populated with the first Build tasks
- Optional: first RUN folder created under `REHYDRATION_PACK/RUNS/`

**Exit criteria:**
- `python scripts/run_ci_checks.py` passes locally
- GitHub Actions `validate` check is green for the PR

## WAVE_B01 — Sprint 0/1 start
**Objective:** Start implementation with low-risk scaffolding.
- confirm local dev workflow (venv, linting, tests)
- initialize backend service skeleton + infra synth
- document required external access (AWS, Richpanel, email, carrier)

## WAVE_B02 — Eventing + persistence foundations
- SQS/SNS/event bus scaffolds (as selected)
- DynamoDB (or selected storage) skeleton tables + migrations story

## WAVE_B03 — Core automation pipeline skeleton
- ingestion → normalization → planning → execution → audit trail
- “dry run” mode and replay support

## WAVE_B04–B10 — Follow the sprint plan
Use:
- `docs/12_Cursor_Agent_Work_Packages/00_Overview/Implementation_Sequence_Sprints.md`

---

# Foundation Waves

## WAVE_F00 — Repo skeleton + governance
- repo layout: docs/, policies/, scripts/, infra/, backend/, frontend/
- base readmes + contribution standards

## WAVE_F01 — Docs/policies scaffold + structure validation
- docs index + doc registry tooling
- initial hygiene + link checks

## WAVE_F02 — Plan + backlog scaffold
- epics/tickets, checklists, runbook outline

## WAVE_F03 — API + data contracts draft
- key domain entities + event payloads defined (draft)

## WAVE_F04 — Infra strategy draft
- deployment approach, environments, secrets strategy

## WAVE_F05 — Backend service blueprint
- service boundaries, modules, integration points

## WAVE_F06 — Frontend/admin blueprint
- minimal ops UI ideas; deferred until backend stabilized

## WAVE_F07 — Security + secrets blueprint
- secrets handling policies + `.env.example` patterns

## WAVE_F08 — Multi-agent GitOps playbook
- branch naming, sequencing, branch budget check

## WAVE_F09 — QA/runbooks baseline
- CI runbook + test strategy scaffolding

## WAVE_F10 — Reference library integration
- reference registry generation + organization

## WAVE_F11 — Doc hygiene + plan sync tooling
- validations and anti-placeholder checks

## WAVE_F12 — Final foundation validation
- full CI-equivalent checks + pack verification

## WAVE_F13 — CR-001: No tracking numbers + delivery estimate-only workflow
- incorporated requirement changes: no tracking numbers, delivery estimates only
- updated docs and plans to reflect “no tracking” constraint

## WAVE_F14 — CR-001 Defer Discovery
- deferred discovery work (explicitly tracked)
- clarified assumptions + updated plan docs to match new scope

## WAVE_F15 — GitHub + CI hardening
- fixed CI failure due to missing `config/.env.example` (tracked + unignored)
- made regen outputs deterministic across platforms:
  - doc registry ordering canonicalized
  - reference registry ordering canonicalized + newline-normalized deterministic `size_bytes`
  - plan checklist banner made deterministic (no date thrash)
- updated CI runbook with PowerShell-safe `gh` patterns
- enabled branch protection and merge settings aligned with repo policy
