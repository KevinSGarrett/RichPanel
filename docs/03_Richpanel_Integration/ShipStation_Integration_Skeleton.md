# ShipStation integration skeleton

- **Secret locations:** ShipStation API credentials live in AWS Secrets Manager under `rp-mw/<env>/shipstation/api_key`, `rp-mw/<env>/shipstation/api_secret`, and (optionally) `rp-mw/<env>/shipstation/api_base`. The `<env>` token follows the shared resolution chain: `RICHPANEL_ENV` → `RICH_PANEL_ENV` → `MW_ENV` → `ENVIRONMENT` → `local`.
- **Client defaults:** `ShipStationClient` is offline-first. Network calls stay blocked (dry-run response) unless `SHIPSTATION_OUTBOUND_ENABLED=true` or `allow_network=True` is passed to the constructor. When blocked, requests exit early with `reason="network_disabled"`.
- **Safety gates:** Callers must pass `safe_mode` and `automation_enabled` flags into `ShipStationClient.request(...)`. The client short-circuits with reasons `safe_mode`, `automation_disabled`, `network_disabled`, or `missing_credentials` so we never emit traffic when gates are closed or credentials are absent.
- **Logging posture:** Request/response logs redact Authorization plus any ShipStation-prefixed headers via `ShipStationClient.redact_headers` to keep shared secrets out of logs.
- **Executor wrapper:** Use `ShipStationExecutor` (modeled after `RichpanelExecutor`) to centralize the outbound gate. It keeps requests in dry-run unless `SHIPSTATION_OUTBOUND_ENABLED=true`, even if an individual worker configures the client differently.
- **Shipments helper:** `ShipStationClient.list_shipments(params=..., safe_mode=..., automation_enabled=...)` wraps a GET to `/shipments`, feeding through the same dry-run and safety gates. Query params are serialized in sorted-key order for deterministic URLs.
- **Enabling network:** Flip `SHIPSTATION_OUTBOUND_ENABLED=true` only in tightly controlled environments. Keep `safe_mode=True` and/or `automation_enabled=False` during rehearsals to preserve the default no-side-effects posture.


