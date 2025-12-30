# Policies Summary (Must Follow)

Canonical policy docs:
- PM policy: `docs/98_Agent_Ops/Policies/POL-PM-001__Adaptive_Project_Manager_Mode_(ChatGPT_Browser).md`
- Agent fix authority: `docs/98_Agent_Ops/Policies/POL-AGENT-001__Agent_Autonomous_Fix_Authority_(Cursor_Agents).md`
- Testing: `docs/98_Agent_Ops/Policies/POL-TEST-001__Agent_Testing_Policy.md`
- Docs coverage: `docs/98_Agent_Ops/Policies/POL-DOCS-001__Documentation_Policy.md`
- Living docs updates: `docs/98_Agent_Ops/Policies/POL-LIVE-001__Living_Docs_Update_Policy.md`
- Structure invariants: `docs/98_Agent_Ops/Policies/POL-STRUCT-001__File-Code-Folder_Layout_Policy.md`
- GitHub/repo ops: `docs/98_Agent_Ops/Policies/POL-GH-001__GitHub_and_Repo_Operations_Policy.md`
- **Project overrides (this project):** `docs/98_Agent_Ops/Policies/POL-OVR-001__Project_Overrides_(Agent_Rules).md`

---

## Key “do not violate” takeaways
- Keep folder structure coherent and predictable.
- Keep the Living Documentation Set current (see `docs/98_Agent_Ops/Living_Documentation_Set.md`).
- No orphan docs/files; everything must be linked from an index/registry.
- No secrets in repo; use AWS Secrets Manager.
- Refactors are allowed **with guardrails** (contracts stable; tests/docs/registries updated).

---

## Mode-aware outputs
- **Foundation mode (`MODE.yaml = foundation`):** run artifacts are not required.
- **Build mode (`MODE.yaml = build`):** each Cursor run must output required artifacts into:
  `REHYDRATION_PACK/RUNS/<RUN_ID>/{A,B,C}/` (templates in `_TEMPLATES/`).

---

## Project-specific overrides (quick)
- 3 Cursor agents: **Agent A/B/C**
- Agents **update docs directly every run**
- Backend runtime: **Python 3.11**
- Admin frontend (planned): **Next.js (TypeScript)**
