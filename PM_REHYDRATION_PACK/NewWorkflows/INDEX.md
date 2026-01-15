# Document index

## Policies (what must be true)

1. `policies/00_ENGINEERING_POLICY_AI_GATES.md`  
   Canonical “operating system” for AI‑only development.

2. `policies/01_RISK_CLASSIFICATION.md`  
   Risk levels, label taxonomy, and how to classify a PR.

3. `policies/02_GATE_MATRIX.md`  
   Exact requirements per risk level (what runs, when, and how it is verified).

4. `policies/03_WAIVERS_AND_EXCEPTIONS.md`  
   When you may override gates and what evidence is required.

5. `policies/04_EVIDENCE_AND_AUDIT.md`  
   Required run artifacts and how to store/point to evidence.

6. `policies/05_SECURITY_PRIVACY_GUARDRAILS.md`  
   Guardrails for secrets/PII and for LLM review tooling (Claude/Bugbot).

7. `policies/06_REPO_POLICY_BRANCH_PROTECTION.md`  
   Repo settings, merge policy, and recommended branch protection strategy.

8. `policies/07_LABEL_TAXONOMY.md`

9. `policies/08_FINDINGS_POLICY.md`  
   Standard labels used to drive automation and enforcement.

---

## Tooling (how each gate works)

- `tooling/BUGBOT_POLICY.md`
- `tooling/CODECOV_POLICY.md`
- `tooling/CLAUDE_REVIEW_POLICY.md`
- `tooling/CLAUDE_PROMPTS.md`
- `tooling/CLAUDE_ACTION_DESIGN.md`
- `tooling/POLICY_GATE_ACTION_DESIGN.md`
- `tooling/CLAUDE_API_SETUP.md`
- `tooling/COST_CONTROLS.md`

---

## Runbooks (how the AI roles operate)

- `runbooks/PM_RUNBOOK.md`
- `runbooks/CURSOR_AGENT_RUNBOOK.md`
- `runbooks/ASSISTANT_MANAGER_RUNBOOK.md`
- `runbooks/TROUBLESHOOTING.md`
- `runbooks/END_TO_END_EXAMPLE.md`
- `runbooks/IMPLEMENTATION_ROLLOUT_PLAN.md`

---

## Templates (drop-in repo assets)

- `templates/.github/pull_request_template.md` → `.github/pull_request_template.md`
- `templates/.github/PULL_REQUEST_TEMPLATE/*` → `.github/PULL_REQUEST_TEMPLATE/*` (optional)
- `templates/PR_CHECKLIST.md`
- `templates/REVIEW_CHECKLIST.md`
- `templates/WAIVER_TEMPLATE.md`
- `templates/RUN_REPORT_SECTION_TEMPLATE.md`

