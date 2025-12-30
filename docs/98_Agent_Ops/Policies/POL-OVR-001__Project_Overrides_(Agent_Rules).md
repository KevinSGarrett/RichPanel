# POL-OVR-001 — Project Overrides (Agent Rules)

Last updated: 2025-12-28 (Wave 01b)

These are **explicit overrides** for this project that sit on top of the imported baseline policies.

If there is conflict:
1) **North Star** (`REHYDRATION_PACK/01_NORTH_STAR.md`) wins  
2) Then this override doc  
3) Then the imported policies

---

## 1) Agents and PM
- PM: ChatGPT in browser.
- Builders: **3 Cursor agents**: **Agent A**, **Agent B**, **Agent C**.

## 2) Docs updates are mandatory and direct
- Agents **may and should update docs directly every run**.
- Every functional change must come with a docs impact map and doc updates.

## 3) Refactors are allowed (guardrails)
Agents may refactor when it:
- reduces complexity,
- reduces future token/search cost,
- or prevents technical debt.

Guardrails:
- keep changes scoped; avoid “big bang” rewrites unless ticket explicitly requires it
- preserve public contracts unless PM explicitly approves change
- tests must remain green; add tests when behavior changes
- update navigation artifacts (`docs/CODEMAP.md`, indexes, registry) if structure changes

## 4) Secrets manager
- Use **AWS Secrets Manager**.
- Never commit secrets; never paste secrets into prompts.

## 5) Frontend planning
- We will include a **frontend/admin console skeleton** in the repo.
- It is not required for v1 routing/automation launch unless later decided.

## 6) Backend runtime (language)
- Default backend runtime: **Python 3.11** (AWS Lambda runtime for v1).
- Primary code home: `backend/` (Python package under `backend/src/`).
- If introducing another language runtime later, document the rationale + update `Decision_Log.md` and `REHYDRATION_PACK/04_DECISIONS_SNAPSHOT.md`.

## 7) Admin frontend framework
- Default admin framework: **Next.js (TypeScript)** under `frontend/admin/`.
- Keep UI work **non-blocking** for v1 routing/automation; do not introduce UI-driven config that bypasses documented policy gates.
- Pin exact npm versions at implementation time (avoid “latest” drift in the repo).

