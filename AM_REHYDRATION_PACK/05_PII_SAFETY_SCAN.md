## PII Safety Scan Patterns

Use these patterns for repository-level greps before shipping run artifacts or proof JSON. They mirror the guardrails in `scripts/dev_e2e_smoke.py`.

- Email/encoded emails: `%40`, `%3C`, `%3E`, `mail.`, `@`, `<`.
- Event identifiers: `evt:[A-Za-z0-9:-]{6,}` (includes follow-up events).
- Ticket numbers: `--ticket-number\\s+\\d+`, `ticket\\s+number\\s+\\d+`.

Example ripgrep commands:

- `rg "evt:[A-Za-z0-9:-]{6,}" REHYDRATION_PACK/`
- `rg "--ticket-number\\s+\\d+" REHYDRATION_PACK/`
- `rg "ticket\\s+number\\s+\\d+" REHYDRATION_PACK/`

Remediation guidance:

- Replace ticket numbers with `ticket fingerprint <fingerprint>`.
- Replace event IDs with `fingerprint:<hash>` or an `event_id_fingerprint` field.
- If a command line is needed, keep `--ticket-number <redacted>` (no digits).
