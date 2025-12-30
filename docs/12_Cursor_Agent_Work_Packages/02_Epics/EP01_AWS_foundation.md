# EP01 — AWS foundation

Last updated: 2025-12-23

## Purpose

Create secure AWS environment boundaries and baseline guardrails without Control Tower.


## Ticket list

- [W12-EP01-T010 — Set up AWS Organization and create dev/staging/prod accounts (Organizations-only)](../03_Tickets/W12-EP01-T010_Set_up_AWS_Organization_and_create_dev_staging_prod_accounts_Organizations_only.md)
- [W12-EP01-T011 — Create IAM roles and least-privilege policies for middleware (ingress vs worker) and CI deploy](../03_Tickets/W12-EP01-T011_Create_IAM_roles_and_least_privilege_policies_for_middleware_ingress_vs_worker_a.md)
- [W12-EP01-T012 — Enable baseline logging + audit (CloudTrail, CloudWatch log retention, budgets, alarms)](../03_Tickets/W12-EP01-T012_Enable_baseline_logging_audit_CloudTrail_CloudWatch_log_retention_budgets_alarms.md)
- [W12-EP01-T013 — Create Secrets Manager + SSM parameter namespaces for env config (including kill switch flags)](../03_Tickets/W12-EP01-T013_Create_Secrets_Manager_SSM_parameter_namespaces_for_env_config_including_kill_sw.md)


## Dependencies

- EP00 (access inventory) recommended.
- EP02 depends on EP01.
