# PM Guardrails (Anti-drift)

Last updated: **2025-12-29** (Wave F06)

These guardrails prevent **process drift** and keep the repo OS stable.

---

## 0) Always respect the current mode

Source of truth:
- `REHYDRATION_PACK/MODE.yaml`

Rules:
- In **foundation** mode, do **not** require Cursor prompts/summaries/run artifacts.
- In **build** mode, enforce RUN artifacts per the manifest.

---

## 1) Canonical navigation

Prefer:
- `docs/INDEX.md` (curated)
- `docs/CODEMAP.md` (structure map)
- `docs/REGISTRY.md` (generated full list)

If a doc is not linked from `docs/INDEX.md`, treat it as supplemental unless proven canonical.

---

## 2) Living docs discipline

If anything changes, update the living docs set:
- `docs/98_Agent_Ops/Living_Documentation_Set.md`
- pointer map: `REHYDRATION_PACK/CORE_LIVING_DOCS.md`

---

## 3) Decision discipline

- Snapshot: `REHYDRATION_PACK/04_DECISIONS_SNAPSHOT.md`
- Canonical log: `docs/00_Project_Admin/Decision_Log.md`

If something is “decided,” record it.

---

## 4) Validation discipline

After meaningful structure/docs updates, run:

```bash
python scripts/verify_rehydration_pack.py
python scripts/regen_doc_registry.py
python scripts/regen_reference_registry.py
python scripts/regen_plan_checklist.py
python scripts/verify_plan_sync.py
python scripts/verify_doc_hygiene.py
```

---

## 5) Agent model (build mode only)

We use three Cursor agents:
- Agent A
- Agent B
- Agent C

In build mode, each agent writes to:
- `REHYDRATION_PACK/RUNS/<RUN_ID>/<AGENT_ID>/`

---

## 6) PM self-hydration (this window)

Prompt helpers:
- `REHYDRATION_PACK/PM_INITIAL_PROMPT.md`
- `REHYDRATION_PACK/PM_REHYDRATION_PROMPT.md`


To prevent drift in the *process of building the repo OS*, maintain:
- `PM_REHYDRATION_PACK/`



---

## GitHub operations guardrails
- Coordinate Git tasks using the run Git plan:
  - `REHYDRATION_PACK/RUNS/<RUN_ID>/GIT_RUN_PLAN.md`
- Default to **sequential** execution if there is any overlap risk.
- Keep branch count low (no branch explosion).
- Do not allow deletions/renames of protected paths unless approved in:
  - `REHYDRATION_PACK/DELETE_APPROVALS.yaml`
- No run is complete until `main` is updated and CI is green.
- Policy of record:
  - `docs/98_Agent_Ops/Policies/POL-GH-001__GitHub_and_Repo_Operations_Policy.md`
