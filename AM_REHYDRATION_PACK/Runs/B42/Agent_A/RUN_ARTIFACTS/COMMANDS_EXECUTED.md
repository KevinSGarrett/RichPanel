# Commands Executed - RUN_20260119_0643Z

## File creation / edits (Cursor apply_patch)
- Add File: `scripts/claude_gate_review.py`
- Update File: `.github/workflows/pr_claude_gate_required.yml`
- Update File: `.github/workflows/seed-secrets.yml`
- Update File: `docs/08_Engineering/CI_and_Actions_Runbook.md`
- Update File: `.github/workflows/pr_risk_label_required.yml`
- Update File: `scripts/claude_gate_review.py` (prompt hardening)
- Update File: `.github/workflows/pr_claude_gate_required.yml` (comment body + permissions)
- Update File: `.github/workflows/pr_risk_label_required.yml` (regex alignment)

## Discovery / verification
```
git status -sb
git remote -v
gh auth status
gh pr status
gh label list --limit 200 | findstr /R /C:"risk:R"
gh label create "risk:R0" --description "R0: docs/comments only; no runtime impact" --color 0e8a16
gh label create "risk:R1" --description "R1: low risk (tests/docs/non-critical code)" --color c2e0c6
gh label create "risk:R2" --description "R2: medium risk (core code paths)" --color fbca04
gh label create "risk:R3" --description "R3: high risk (security/PII/payments/infra)" --color d93f0b
gh label create "risk:R4" --description "R4: critical (prod safety / auth / secrets / compliance)" --color b60205
powershell -NoProfile -Command "(Get-Date).ToUniversalTime().ToString('yyyyMMdd_HHmmZ')"
```

## Git operations
```
git checkout -b run/RUN_20260119_0643Z_claude_gate_real
git add .github/workflows/pr_claude_gate_required.yml .github/workflows/pr_risk_label_required.yml .github/workflows/seed-secrets.yml docs/08_Engineering/CI_and_Actions_Runbook.md scripts/claude_gate_review.py
git commit -m "RUN:RUN_20260119_0643Z real Claude gate + Shopify secrets"
git push -u origin run/RUN_20260119_0643Z_claude_gate_real

git add .github/workflows/pr_claude_gate_required.yml
git commit -m "Fix Claude gate comment permissions"
git push

git add .github/workflows/pr_claude_gate_required.yml
git commit -m "Fix Claude gate comment body upload"
git push

git add scripts/claude_gate_review.py
git commit -m "Harden Claude gate prompt against false positives"
git push

git add .github/workflows/pr_risk_label_required.yml
git commit -m "Align risk label regex with Claude gate"
git push

python scripts/run_ci_checks.py
git add docs/00_Project_Admin/To_Do/_generated/PLAN_CHECKLIST_EXTRACTED.md docs/00_Project_Admin/To_Do/_generated/plan_checklist.json docs/_generated/doc_outline.json docs/_generated/doc_registry.compact.json docs/_generated/doc_registry.json docs/_generated/heading_index.json
git commit -m "Update generated docs"
git push
```

## PR creation / labels / comments / checks
```
gh pr create --title "RUN:RUN_20260119_0643Z real Claude gate + Shopify secrets" --body "## Objective
Implement real Claude gate w/ Anthropic API, add Shopify Secrets Manager seeding, update CI runbook.

## Evidence (to be filled after checks)
- Risk label + model: TBD
- Actions run (Claude gate): TBD
"
gh pr edit 123 --add-label "risk:R2" --add-label "gate:claude"
gh pr edit 123 --remove-label "risk:R2" --add-label "risk:R1"
gh pr edit 123 --body-file .\_tmp_pr_body.txt
gh pr comment 123 -b "Bugbot resolution: aligned risk label regexes so both workflows now require a suffix after '-' or '_' (e.g., risk:R1-low). Updated `pr_risk_label_required.yml` to match `claude_gate_review.py`."
gh pr comment 123 -b "@cursor review"
gh pr checks 123
```

## GitHub Actions runs
```
gh run list --workflow pr_claude_gate_required.yml --branch run/RUN_20260119_0643Z_claude_gate_real --limit 5
gh run watch <run-id> --exit-status
gh run view <run-id> --log
gh run rerun 21128713442 --failed

gh run list --workflow ci.yml --branch run/RUN_20260119_0643Z_claude_gate_real --limit 5
gh run watch 21128481550 --exit-status
gh run view 21128481550 --log
```

## Branch protection update
```
gh api repos/KevinSGarrett/RichPanel/branches/main/protection/required_status_checks
$body = @'
{"strict": true, "contexts": ["validate", "claude-gate-check"]}
'@
$body | Set-Content -Path .\_tmp_required_status_checks.json
gh api --method PATCH repos/KevinSGarrett/RichPanel/branches/main/protection/required_status_checks --input .\_tmp_required_status_checks.json
Remove-Item .\_tmp_required_status_checks.json
```

## Shopify seeding workflows
```
gh workflow run seed-secrets.yml -f environment=dev
gh workflow run seed-secrets.yml --ref run/RUN_20260119_0643Z_claude_gate_real -f environment=dev
gh workflow run seed-secrets.yml --ref run/RUN_20260119_0643Z_claude_gate_real -f environment=staging
gh workflow run seed-secrets.yml --ref run/RUN_20260119_0643Z_claude_gate_real -f environment=prod
gh run list --workflow seed-secrets.yml --branch run/RUN_20260119_0643Z_claude_gate_real --limit 1 --json databaseId,url,status,conclusion,createdAt --jq '.[0]'
gh run watch <run-id> --exit-status
gh run view <run-id> --log
```
