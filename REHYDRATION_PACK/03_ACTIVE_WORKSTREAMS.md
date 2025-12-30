# Active Workstreams

Last updated: 2025-12-29 (Wave F13)

**Current mode:** foundation (see `REHYDRATION_PACK/MODE.yaml`)  
Focus is documentation OS readiness; implementation begins in build mode.

---

## Stream F1 — Docs indexing + registries ✅ DONE
- `docs/REGISTRY.md` + generated JSON indexes
- heading-level lookup (`docs/_generated/heading_index.json`)
- navigation hardened (`docs/INDEX.md`, `docs/CODEMAP.md`)

## Stream F2 — Rehydration pack automation ✅ DONE
- mode-aware manifest + verifier (`scripts/verify_rehydration_pack.py`)
- pack templates ready for build mode

## Stream F3 — Policy + template hardening ✅ DONE
- agent policy overrides
- living docs set defined
- standardized templates for decisions/issues/tests

## Stream F4 — Foundation readiness (Wave F06) ✅ DONE
- build-mode activation checklist created
- plan → checklist extraction added (generated views)
- legacy redirect folders standardized

## Stream F5 — Doc hygiene cleanup (Wave F08) ✅ DONE
- Removed ambiguous placeholder markers (`...` and `…`) from INDEX-linked canonical docs
- `python scripts/verify_doc_hygiene.py` now passes with no warnings

---

## Current next focus — Build-mode activation
- `REHYDRATION_PACK/FOUNDATION_STATUS.md`
- `docs/00_Project_Admin/Build_Mode_Activation_Checklist.md`
- `REHYDRATION_PACK/05_TASK_BOARD.md`


## Stream F6 — Schedule + phase clarity ✅ DONE
- Foundation vs Build clarified in `REHYDRATION_PACK/WAVE_SCHEDULE_FULL.md`
- Legacy wave mapping preserved in `docs/00_Project_Admin/Wave_Naming_and_Mapping.md`

## Stream F13 — CR-001 No-tracking delivery estimates (order status)
- Spec + templates added (foundation)
- Pending: data mapping confirmation (shipping method strings, preorder ETA source) + Richpanel resolve/reopen semantics
