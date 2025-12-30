# Richpanel Reference Library

Last updated: 2025-12-29

Source: `03_Richpanel_Documentation.zip` (imported into `Non_Indexed_Library/`).

This folder contains **vendor/reference material** used to implement Richpanel middleware safely.

## Start here

- [Top 20 docs](TOP_20.md) — fastest way to find the right vendor doc
- Machine registry (full coverage):
  - `reference/richpanel/_generated/reference_registry.json` (**359 files**) 

## Topic buckets (human-friendly)

These buckets map to the raw folder structure under `Non_Indexed_Library/`.

| Bucket | Files | When to use |
|---|---:|---|
| `Richpanel Middleware Documentation` | 2 | High-level vendor docs; good first orientation. |
| `Developing Middleware for Richpanel Comprehensive Guide` | 47 | Implementation best practices (ACK-fast, security, loops, reliability). |
| `Richpanel_Integration` | 57 | Practical integration notes: HTTP targets, triggers, routing, retries, rollout. |
| `API` | 158 | Richpanel API reference + endpoint families + auth/errors/limits. |
| `Order_Event_Structure` | 5 | Order event payload + sample objects. |
| `Subscription_Event_Structure` | 4 | Subscription event payload + sample objects. |
| `SendMessage` | 2 | Notes/examples for sending messages. |
| `CurrentSetup` | 53 | Reference for fields/tags/macros/automation inventory in current setup. |
| `Common Issues` | 20 | Known pitfalls: loops, automation surprises, edge cases. |
| `DRP` | 1 | Disaster recovery planning notes (small). |

---

## Recommended entry docs by bucket

### Richpanel Middleware Documentation
- [Richpanel Middleware Documentation](Non_Indexed_Library/Richpanel Middleware Documentation/Richpanel Middleware Documentation.txt)
- [Richpanel AI Middleware – Integration](Non_Indexed_Library/Richpanel Middleware Documentation/Richpanel AI Middleware – Integration.txt)

### Developing Middleware for Richpanel Comprehensive Guide
- [Overview](Non_Indexed_Library/Developing Middleware for Richpanel Comprehensive Guide/Overview.txt)
- [Receiving the Webhook — Acknowledge Quickly](Non_Indexed_Library/Developing Middleware for Richpanel Comprehensive Guide/Receiving the Webhook in Your Middleware/Acknowledge Quickly.txt)
- [Avoiding Automation Loops — Tag-Based Flags](Non_Indexed_Library/Developing Middleware for Richpanel Comprehensive Guide/Avoiding Automation Loops/Tag-Based Flags.txt)

### Richpanel_Integration
- [Official integration entry points — Stability](Non_Indexed_Library/Richpanel_Integration/Official_Integration_Entry_Points/Stability.txt)
- [HTTP target payload — Including IDs and Deduplication Keys](Non_Indexed_Library/Richpanel_Integration/HTTP Target Payload and Available Fields/Including IDs and Deduplication Keys.txt)
- [Reliability — Delivery Guarantees for HTTP Targets](Non_Indexed_Library/Richpanel_Integration/Reliability and Retries of HTTP Targets & API Calls/Delivery Guarantees for HTTP Targets.txt)
- [Routing primitives — Department concept](Non_Indexed_Library/Richpanel_Integration/Routing Primitives Teams (Departments) and Ticket Assignment/Department_Concept.txt)

### API
- [Getting started](Non_Indexed_Library/API/Getting_Started_RichPanel_API.txt)
- [Authentication](Non_Indexed_Library/API/Authentication.txt)
- [Errors](Non_Indexed_Library/API/Errors.txt)
- [Limitations](Non_Indexed_Library/API/Limitations.txt)

### Event payload structure
- [Sample order event](Non_Indexed_Library/Order_Event_Structure/Sample_Order_Event.txt)
- [Order properties](Non_Indexed_Library/Order_Event_Structure/Order_Properties.txt)
- [Subscription event](Non_Indexed_Library/Subscription_Event_Structure/Subscription_Event.txt)

### Current setup
- [Automation overview](Non_Indexed_Library/CurrentSetup/Automation/Overview.txt)
- [Tags overview](Non_Indexed_Library/CurrentSetup/Tags/Overview.txt)

### Common issues
- [Automation loops](Non_Indexed_Library/Common Issues/Automation loops.txt)
- [Automation pitfalls](Non_Indexed_Library/Common Issues/Automation pitfalls.txt)

---

## How this library connects to the project plan

Canonical implementation specs live in:
- `docs/03_Richpanel_Integration/`

Use the crosswalk:
- `docs/03_Richpanel_Integration/Vendor_Doc_Crosswalk.md`

When updating canonical specs, prefer to cite vendor docs by:
- link to the specific `.txt` in `Non_Indexed_Library/`
- plus the exact section title (first line) if available
