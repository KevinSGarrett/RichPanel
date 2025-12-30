# Agent Testing Policy

**Doc ID:** POL-TEST-001  
**Source:** `Policies.zip` (extended/hardened in Wave F05)  
**Last verified:** 2025-12-29  

## Core rule
You must **prove correctness** for every change you make.

## Required: define the “touched surface area”
- List every file/module/API/workflow you changed (from git diff).
- List impacted components (direct + likely indirect dependencies).
- If unsure, assume impact is broad and test broadly.

## Evidence is required (no exceptions)
For any tests you run, record evidence in:
- `docs/08_Testing_Quality/Test_Evidence_Log.md`
And store raw artifacts in:
- `qa/test_evidence/` (preferred) or `artifacts/`

Each evidence entry must include:
- Exact commands executed (copy/paste)
- Results summary (pass/fail counts)
- Environment (local/CI)
- Link/path to artifacts

Template:
- `docs/98_Agent_Ops/Templates/Test_Evidence_Entry_TEMPLATE.md`

## No “green by cheating”
- Do not disable tests, loosen assertions, skip suites, or increase timeouts to hide failures.
- If a test is flaky, fix it or isolate it deterministically.

## If you cannot run required tests
Stop and report:
- Exactly what you tried
- Why it failed (env/config/permissions)
- What would be needed to run the tests

## When to create an issue
- If something breaks or fails unexpectedly, create:
  - a new issue file in `docs/00_Project_Admin/Issues/`
  - update `docs/00_Project_Admin/Issue_Log.md`
