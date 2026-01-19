# B42 Agent C - Evidence Artifacts

## Purpose
This folder contains evidence from live read-only shadow evaluation testing.

## Contents

### Artifacts (`artifacts/`)
- `20260119T181208Z_91608.json` - Prod key test, ticket 91608
- `20260119T175715Z_1042.json` - Sandbox key test, ticket 1042

Both artifacts are PII-safe (see PII_SAFETY_REPORT.md).

### Logs (`logs/`)
- `run_20260119T181208Z_ticket_91608.log` - Full console output, prod key run
- `run_20260119T175715Z_ticket_1042.log` - Full console output, sandbox run

Logs prove:
- Write self-check passed (RichpanelWriteDisabledError raised)
- Env vars enforced (MW_ALLOW_NETWORK_READS=true, etc.)
- Only GET requests made (no writes)

### PII Safety Report
- `PII_SAFETY_REPORT.md` - Detailed inspection confirming no PII in artifacts

## How to Verify
1. Read `PII_SAFETY_REPORT.md`
2. Inspect artifact JSONs directly
3. Review logs for self-check PASS and GET-only requests
