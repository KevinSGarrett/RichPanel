# Build Mode Activation Checklist

Last verified: 2025-12-29 — Wave F06.

This checklist defines what must be true before switching:
- `REHYDRATION_PACK/MODE.yaml` from `foundation` → `build`

**Goal:** when build mode starts, AI agents can work in a tight loop without missing context, breaking ops hygiene, or leaking sensitive data.

---

## A) Documentation OS readiness (foundation exit criteria)

- [x] REHYDRATION_PACK exists and validates (`python scripts/verify_rehydration_pack.py`)
- [x] Docs registry + heading index generation works (`python scripts/regen_doc_registry.py`)
- [x] Reference registry generation works (`python scripts/regen_reference_registry.py`)
- [x] Living documentation set is defined and linked from `docs/INDEX.md`
- [x] Policies/templates exist and are unambiguous
- [x] Plan checklist extraction exists (Wave F06) and can be regenerated
- [ ] Canonical docs do not contain ambiguous placeholders (run hygiene checks; resolve warnings)

---

## B) Repo operational readiness (before first build run)

- [ ] AWS account + region(s) confirmed for dev/staging/prod
- [ ] Secrets strategy confirmed (AWS Secrets Manager) and access patterns documented
- [ ] CI baseline chosen (GitHub Actions recommended) and minimal pipeline stub exists
- [ ] “No secrets in repo” is enforced (pre-commit or CI check)

---

## C) Integration readiness (before going live)

*(These can be completed incrementally, but must be tracked explicitly.)*

- [ ] Richpanel tenant verification items resolved (HTTP targets, headers, templating constraints)
- [ ] Webhook authentication strategy confirmed and documented
- [ ] Shopify integration assumptions verified (fields + APIs)
- [ ] Legal/privacy review complete for data handling

---

## D) Build mode switch procedure

1) Update `REHYDRATION_PACK/MODE.yaml`:
   - set `mode: build`
   - set `current_wave: "WAVE_B00"` (or first build wave)
2) Populate `REHYDRATION_PACK/06_AGENT_ASSIGNMENTS.md` with the first run set prompts
3) Ensure `REHYDRATION_PACK/RUNS/` has the first run folder and templates
4) Run verifiers:
   - `python scripts/verify_rehydration_pack.py --strict`
   - `python scripts/verify_plan_sync.py`

