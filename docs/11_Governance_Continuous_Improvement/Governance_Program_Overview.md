# Governance Program Overview

Last updated: 2025-12-22

Governance is how we ensure this system stays **accurate, safe, and useful** over time — even as:
- new products/issues appear
- agent processes change
- models change
- volumes spike
- business priorities shift

This wave turns the project from “we built it” into “we can operate it sustainably.”


**Start here:** `docs/11_Governance_Continuous_Improvement/Governance_Quick_Start.md`  
**Monthly cadence:** `docs/11_Governance_Continuous_Improvement/Governance_Audit_Checklist.md`

---

## What governance covers (v1 scope)

### 1) Quality governance
- routing quality (correct team / tag)
- FAQ automation quality (correct template, correct variables, correct policy gates)
- Tier policy enforcement (Tier 0 always safe; Tier 2 deterministic match)

### 2) Safety and privacy governance
- what data is logged and retained
- how we prevent accidental disclosure
- how we respond to “wrong reply” incidents

### 3) Change governance
- how prompts/templates/taxonomy/thresholds change
- how we test and approve changes
- how we release progressively and roll back safely

### 4) Vendor governance
- OpenAI/Richpanel/Shopify changes and outages
- rate limits and cost changes
- deprecations and migration plans

---

## Governance principles (non-negotiable)

1) **Policy gates are authoritative.**  
   The model recommends; the system decides.

2) **Fail closed by default.**  
   If unsure, route to a human; do not auto-reply with sensitive info.

3) **All production behavior is versioned.**  
   Templates, prompts, schemas, thresholds, and mappings must be traceable.

4) **Small reversible changes beat large risky ones.**  
   Prefer thresholds and template enablement flags before prompt/taxonomy refactors.

5) **Human feedback is a first-class signal.**  
   Agent override tags/macros are critical for continuous improvement.

---

## Primary governance artifacts (where decisions live)

- **Decision Log:** `docs/00_Project_Admin/Decision_Log.md`
- **Change Log:** `docs/00_Project_Admin/Change_Log.md`
- **Risk Register:** `docs/00_Project_Admin/Risk_Register.md`
- **Golden Set SOP:** `docs/04_LLM_Design_Evaluation/Golden_Set_Labeling_SOP.md`
- **Change Management:** `docs/11_Governance_Continuous_Improvement/Change_Management.md`
- **Model Update Policy:** `docs/11_Governance_Continuous_Improvement/Model_Update_Policy.md`
- **Taxonomy Drift & Calibration:** `docs/11_Governance_Continuous_Improvement/Taxonomy_Drift_and_Calibration.md`

---

## Recommended governance roles (v1 defaults)

These are suggested defaults and can be adjusted as your org evolves.

- **Governance Owner (Accountable):** Engineering lead (you)  
- **Support Ops Owner (Accountable for copy + macros):** Support lead / operations
- **Quality Owner (Responsible):** assigned engineer or analyst (can be part-time early)
- **Security/Privacy Reviewer (Consulted):** engineering/security

A full RACI is in `Artifact_Ownership_RACI.md`.

---

## What “success” means
Governance is successful when:
- changes are safe and fast (no fear of breaking production)
- metrics improve over time (routing accuracy, deflection, lower overrides)
- incidents lead to permanent fixes (tests, gates, runbooks), not repeated firefighting

