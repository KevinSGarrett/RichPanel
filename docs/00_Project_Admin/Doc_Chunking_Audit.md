# Documentation Chunking Audit

Last updated: 2025-12-29

Purpose: highlight documentation files that may be hard for AI workers to retrieve or reason about due to missing structure (headings) or overly large size.

---

## 0) Summary metrics

- Total markdown docs under `docs/` (excluding `docs/_generated`): **346**
- Docs linked from `docs/INDEX.md`: **130**
- Indexed docs with **no** H2 sections: **0**
- All docs with **no** H2 sections (non-legacy sections only): **11**
- Docs > 900 lines: **0** (current library is within the recommended size cap)

---

## 1) Indexed docs with no H2 headings

✅ None. All docs linked from `docs/INDEX.md` contain structured sections (Wave F04).

---

## 2) Non-legacy docs with no H2 headings (candidates for improvement)

These files are not in legacy folders, but currently have only an H1 (or minimal structure).

- `03_Richpanel_Integration/Attachments_Playbook.md`
- `06_Security_Privacy_Compliance/Security_Controls_Matrix.md`
- `12_Cursor_Agent_Work_Packages/04_Cursor_Run_Prompts/00_Cursor_Run_Output_Requirements.md`
- `90_Risks_Common_Issues/FMEA.md`
- `90_Risks_Common_Issues/Threat_Model.md`
- `98_Agent_Ops/Policies/POL-AGENT-001__Agent_Autonomous_Fix_Authority_(Cursor_Agents).md`
- `98_Agent_Ops/Policies/POL-DOCS-001__Documentation_Policy.md`
- `98_Agent_Ops/Policies/POL-PM-001__Adaptive_Project_Manager_Mode_(ChatGPT_Browser).md`
- `98_Agent_Ops/Policies/POL-STRUCT-001__File-Code-Folder_Layout_Policy.md`
- `98_Agent_Ops/Policies/POL-TEST-001__Agent_Testing_Policy.md`
- `99_Appendices/Glossary.md`

Recommended fix pattern (when you touch these files):
- add stable H2 headings like:
  - `## 0) Purpose`
  - `## 1) Scope`
  - `## 2) Procedure / Details`

Note: policy docs will be normalized in **Wave F05** (policy + template hardening).
