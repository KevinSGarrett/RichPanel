# Wave 2 — System architecture & infrastructure decisions

Last updated: 2025-12-21
Last verified: 2025-12-21 — Added DynamoDB schema, rate limiting, cost model inputs, and failure-mode skeleton.

## Goals
1) Select the **best default hosting stack** (AWS) for this project that optimizes:
   - reliability + correctness
   - speed of iteration
   - low operational overhead
   - cost efficiency at current volume, with headroom for growth
2) Define the **production reference architecture** (components + data flow + responsibilities).
3) Establish **baseline SLOs/SLAs** (especially latency) for an early rollout.
4) Identify infra-level risks (rate limits, retries, duplicate events, cold starts) and bake mitigations into the plan.

## Deliverables (this wave)
### Architecture decisions
- ✅ Hosting decision: AWS Serverless (API Gateway + Lambda + SQS FIFO + DynamoDB)
- ✅ Primary region (v1): `us-east-2` (DR optional later)
- ✅ Environment strategy: separate AWS accounts (`dev` / `staging` / `prod`) under AWS Organizations
  - ✅ Control Tower deferred for v1 (Organizations-only)
  - ✅ AWS Organizations management account owner: **you (developer)**

### Architecture docs updated/created
- ✅ `docs/02_System_Architecture/Hosting_Options_and_Recommendation.md`
- ✅ `docs/02_System_Architecture/Architecture_Overview.md`
- ✅ `docs/02_System_Architecture/AWS_Serverless_Reference_Architecture.md`
- ✅ `docs/02_System_Architecture/AWS_Region_and_Environment_Strategy.md`
- ✅ `docs/02_System_Architecture/AWS_Organizations_Setup_Plan_No_Control_Tower.md`
- ✅ `docs/02_System_Architecture/DynamoDB_State_and_Idempotency_Schema.md`
- ✅ `docs/02_System_Architecture/Sequence_Diagrams.md`
- ✅ `docs/02_System_Architecture/Data_Flow_and_Storage.md`

### Reliability/cost foundations updated
- ✅ `docs/07_Reliability_Scaling/Capacity_Plan_and_SLOs.md` (uses real 7-day heatmap totals)
- ✅ `docs/07_Reliability_Scaling/Rate_Limiting_and_Backpressure.md`
- ✅ `docs/07_Reliability_Scaling/Cost_Model.md` (formula-based; placeholders for vendor pricing)
- ✅ `docs/07_Reliability_Scaling/Failure_Modes_and_Recovery.md` (v1 skeleton)

## Status
- ✅ **Complete** (Wave 02 closed)

## Final decisions locked in this wave
- ✅ v1 audit trail: **logs-only** (skip optional DynamoDB `rp_mw_audit_actions` table in v1)
- ✅ v1 queue strategy: **single SQS FIFO queue** (no separate LiveChat lane in v1)

## Dependencies handed off to next waves (tracked, not blocking Wave 02)
- Richpanel trigger type + payload schema (Wave 03)
- Shopify Admin API fallback access (Wave 05)
## Progress notes
- Updated architecture to explicitly enforce ACK-fast + idempotency + backpressure.
- Added cost model inputs from the real heatmap dataset so we can reason about scale early.
