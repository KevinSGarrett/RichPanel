# Incident communications templates

Last updated: 2025-12-22

These are templates for internal and customer-facing comms during incidents.

Important:
- Avoid customer PII in internal broad channels.
- For customer-facing statements, do not disclose sensitive details.

---

## Internal incident update (Slack/email)

**Subject:** [SEV-X] Middleware incident — <short description>

**Status:** Investigating / Mitigating / Monitoring / Resolved  
**Start time:** <timestamp>  
**Impact:** <routing delayed / wrong replies / automation disabled>  
**Customer risk:** <low/medium/high>

**What we know:**
- <bullet list>

**What we’re doing now:**
- <bullet list>
- Lever state:
  - safe_mode = <true/false>
  - automation_enabled = <true/false>

**Next update:** <timestamp>

---

## Leadership escalation update

**Subject:** [SEV-0/1] Customer-impacting incident — decision needed

**Summary (1–2 sentences):**  
<what happened>

**Customer impact:**  
<scope, channels, estimated volume>

**Risk:**  
<PII risk? chargebacks? refunds?>

**Mitigation applied:**  
<safe_mode / automation disabled / vendor throttling>

**Decision needed:**  
<e.g., approve customer messaging / refunds policy / temporarily shut off automation>

---

## Support Ops guidance to agents

**Message:**  
We’re currently experiencing <issue>.  
Please do the following until further notice:
- Treat tickets with `mw:routed:true` as a suggestion; confirm intent manually.
- Do not rely on automation replies; reply manually using macros.
- If you see suspicious automation behavior, tag `mw:feedback:pii_risk` and escalate.

---

## Customer-facing acknowledgement (optional)
Use only if you decide to proactively message customers:

“We’re currently experiencing a delay with some support responses. Our team is working to resolve this as quickly as possible. Thank you for your patience.”

Avoid mentioning internal vendors, AI, or specifics unless required by policy.

---

## Post-incident customer follow-up (optional)
If automation caused incorrect guidance:

“We’re sorry — a system issue may have caused an incorrect response. Our team has reviewed your request and will follow up with the correct information shortly.”
