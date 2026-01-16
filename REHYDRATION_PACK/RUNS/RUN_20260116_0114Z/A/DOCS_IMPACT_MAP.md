# Docs Impact Map - B40 Delta

**Run ID:** RUN_20260116_0114Z  
**Agent:** A  
**Date:** 2026-01-16

## Purpose

This delta run fixed 3 Bugbot Medium findings in drop-in workflow examples (PM policy pack). Changes affect example workflows that demonstrate the NewWorkflows gate strategy for adopters.

## Files Modified

### Drop-in Workflows (4 files)

#### 1. gated-quality.yml
**Path:** `PM_REHYDRATION_PACK/NewWorkflows/Drop_In_Patch/drop_in/.github/workflows/gated-quality.yml`  
**Type:** Example workflow (PM policy pack)  
**Changes:**
- **Fixed label state logic (mark-gates job):**
  - Old: Only removed `gates:ready` and `gates:failed`; didn't remove `stale:gates` on failure
  - New: Always removes `gates:ready` and `gates:stale` after run; properly handles `gates:passed`/`gates:failed` based on outcome
- **Unified risk label taxonomy:**
  - Old: `risk:R0`, `risk:R1`, `risk:R2`, `risk:R3`, `risk:R4`
  - New: `risk:R0-docs`, `risk:R1-low`, `risk:R2-medium`, `risk:R3-high`, `risk:R4-critical`
- **Fixed gate label name:**
  - Old: `stale:gates`
  - New: `gates:stale`

**Bugbot finding addressed:** #1 (Medium - label handling logic)

#### 2. policy-gate.yml
**Path:** `PM_REHYDRATION_PACK/NewWorkflows/Drop_In_Patch/drop_in/.github/workflows/policy-gate.yml`  
**Type:** Example workflow (PM policy pack)  
**Changes:**
- **Fixed check-run map construction:**
  - Old: `const byName = new Map(runs.map(r => [String(r.name), r]))` - retains last (oldest) run if duplicates
  - New: Iterate runs and only set map entry if not already present - keeps first (newest) run
- **Unified risk label taxonomy:** Same as gated-quality.yml
- **Fixed gate label name:** `stale:gates` → `gates:stale`

**Bugbot finding addressed:** #2 (Medium - check-run selection)

#### 3. seed-gate-labels.yml
**Path:** `PM_REHYDRATION_PACK/NewWorkflows/Drop_In_Patch/drop_in/.github/workflows/seed-gate-labels.yml`  
**Type:** Example workflow (PM policy pack)  
**Changes:**
- **Updated label definitions to match repo docs:**
  - Risk labels: `risk:R0-docs`, `risk:R1-low`, `risk:R2-medium`, `risk:R3-high`, `risk:R4-critical`
  - Gate label: `gates:stale` (not `stale:gates`)
- **Descriptions updated to match Quality_Gates_and_Risk_Labels.md taxonomy**

**Bugbot finding addressed:** #3 (Medium - taxonomy consistency)

#### 4. gates-staleness.yml
**Path:** `PM_REHYDRATION_PACK/NewWorkflows/Drop_In_Patch/drop_in/.github/workflows/gates-staleness.yml`  
**Type:** Example workflow (PM policy pack)  
**Changes:**
- **Fixed gate label references:**
  - Old: `stale:gates`
  - New: `gates:stale`
- **Updated comments and log messages to use correct label name**

**Bugbot finding addressed:** #3 (Medium - taxonomy consistency)

### PM Tracker (1 file)

#### Progress_Log.md
**Path:** `docs/00_Project_Admin/Progress_Log.md`  
**Previous last verified:** 2026-01-15 - RUN_20260115_2224Z  
**New last verified:** 2026-01-16 - RUN_20260116_0114Z  
**Changes:**
- Added entry for RUN_20260116_0114Z documenting Bugbot fixes
- Moved to top of Timeline section (most recent first)

### Auto-Regenerated (4 files)

**Files:**
- `docs/_generated/doc_outline.json`
- `docs/_generated/doc_registry.compact.json`
- `docs/_generated/doc_registry.json`
- `docs/_generated/heading_index.json`

**Reason:** Progress_Log.md update triggered registry rebuild

## No Changes to Active Repo Workflows

**Important:** The modified files are in `PM_REHYDRATION_PACK/NewWorkflows/Drop_In_Patch/drop_in/.github/workflows/` (example workflows in PM policy pack), NOT in the active repo `.github/workflows/` folder.

These are **reference examples** for adopters, not active workflows in this repository.

## Integration Points

### Documents that reference the drop-in pack:
- `PM_REHYDRATION_PACK/NewWorkflows/README.md` - mentions drop-in workflows
- `docs/08_Engineering/Quality_Gates_and_Risk_Labels.md` - defines the label taxonomy these workflows now match

### Consistency achieved:
✓ Drop-in workflow risk labels now match repo docs (`risk:R#-level`)  
✓ Drop-in workflow gate labels now match repo docs (`gates:stale`)  
✓ Label state transitions now follow documented logic  
✓ Check-run selection now uses newest run (correct behavior)

## Backward Compatibility

### Breaking changes:
- None (these are example workflows, not production)

### Additive changes:
- Fixed examples now demonstrate correct patterns
- Adopters who copy these workflows will get the correct label taxonomy

## Validation

✅ All modified files validated through Bugbot review (GREEN)  
✅ No broken references (all labels match documented taxonomy)  
✅ CI-equivalent checks passed  
✅ Progress_Log entry properly formatted and indexed

## Next Documentation Steps

1. If adopting drop-in workflows in future, use the fixed versions
2. Patch files in `Drop_In_Patch/patches/` could be regenerated to match (lower priority, workflows themselves are authoritative)
3. Future NewWorkflows documentation should reference the corrected label taxonomy

## Summary

This delta run ensured the drop-in workflow examples in the PM policy pack match the label taxonomy documented in `Quality_Gates_and_Risk_Labels.md` and implement correct label state logic. All 3 Bugbot findings addressed with zero impact on active repo workflows (changes are in example/reference files only).
