# Security & Privacy — Index

Last verified: 2025-12-29 — Wave F05.

This folder is the canonical home for security, privacy, and compliance documentation.

## Start here
- `Security_Privacy_Compliance_Overview.md`

## Core documents
- PII handling and redaction: `PII_Handling_and_Redaction.md`
- Secrets management: `Secrets_and_Key_Management.md`
- Request validation: `Webhook_Auth_and_Request_Validation.md`
- Threat model: `Threat_Model_STRIDE.md`
- Controls matrix: `Security_Controls_Matrix.md`

## Runbooks
- Incident response: `Incident_Response_Security_Runbooks.md`
- Webhook secret rotation: `Webhook_Secret_Rotation_Runbook.md`
- Kill switch and safe mode: `Kill_Switch_and_Safe_Mode.md`

## Update rules
If you change anything that affects data handling, authentication, secrets, or logging:
- Update relevant docs here
- Update `docs/02_System_Architecture/System_Matrix.md`
- Update `CHANGELOG.md`
