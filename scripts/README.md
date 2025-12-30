# Scripts — Repo Automation

Last verified: 2025-12-29

These scripts are part of the repo’s **AI-first operating system**:
- deterministic regeneration of indexes/registries
- validation of the documentation system
- build-mode rehydration pack enforcement
- Git/GitHub guardrails for multi-agent work

All scripts are **standard library only** (no external dependencies).

---

## Foundation mode: core commands

### Validate the rehydration pack
```bash
python scripts/verify_rehydration_pack.py
```

### Regenerate registries
```bash
python scripts/regen_doc_registry.py
python scripts/regen_reference_registry.py
python scripts/regen_plan_checklist.py
```

### Validate docs + references
```bash
python scripts/verify_plan_sync.py
python scripts/verify_doc_hygiene.py
```

---

## Build mode: run folder scaffolding

Create the standard build-mode run skeleton:
```bash
python scripts/new_run_folder.py --now
```

This creates:
- `REHYDRATION_PACK/RUNS/<RUN_ID>/RUN_META.md`
- `REHYDRATION_PACK/RUNS/<RUN_ID>/GIT_RUN_PLAN.md`
- `REHYDRATION_PACK/RUNS/<RUN_ID>/{A,B,C}/...` templates

---

## CI-equivalent checks (agents must run before pushing)

Run:
```bash
python scripts/run_ci_checks.py
```

In GitHub Actions, run:
```bash
python scripts/run_ci_checks.py --ci
```

---

## Git safety guardrails

### Protected delete check
Fails if you delete/rename protected paths without approval:
```bash
python scripts/check_protected_deletes.py
```

Approvals live in:
- `REHYDRATION_PACK/DELETE_APPROVALS.yaml`

### Branch budget check (prevents branch explosion)
```bash
python scripts/branch_budget_check.py
```

---

## Notes
- The authoritative rules live in:
  - `docs/98_Agent_Ops/Policies/`
- The operating playbooks live in:
  - `docs/08_Engineering/`
