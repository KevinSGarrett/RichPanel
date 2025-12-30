# Procedures: Adding New Intents, Teams, or Templates

Last updated: 2025-12-22

This document provides step-by-step playbooks for extending the system safely.

---

## A) Add a new routing intent

1. Create an intent proposal
   - name, definition, examples, non-examples
   - target department/team mapping
2. Update taxonomy + labeling guide
3. Update multi-intent priority matrix if needed
4. Add to golden set labeling workflow (sample + label)
5. Update routing mappings and training guide
6. Run eval + smoke tests
7. Roll out progressively (route-only first)

---

## B) Add a new department/team
1. Create the team in Richpanel (or tag-based virtual queue)
2. Add mapping in routing table
3. Add monitoring for mapping drift
4. Update agent training materials
5. Run staging smoke tests

---

## C) Add a new FAQ automation template_id
1. Determine tier eligibility (Tier 1 vs Tier 2 only)
2. Add template_id to Template_ID_Catalog
3. Add copy to `templates_v1.yaml` (default + livechat, email if needed)
4. Define required variables (and how they’re obtained safely)
5. Add test cases to smoke pack
6. Roll out:
   - route-only first
   - then Tier 1 safe-assist
   - Tier 2 only if deterministic match exists

---

## D) Retire an intent or template
1. Disable template_id (kill switch per-template)
2. Keep mapping for historical data (do not delete immediately)
3. Update docs and training
4. Monitor for “unknown intent” rate increases

