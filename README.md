# Trucking Software Research

## Governing Question

**Where does trucking software use predictions, risk, and constraints to govern economic opportunity?**

## Purpose

This repository studies trucking as a software system before attempting to build software for it.

The goal is to identify where algorithms, data, prediction, and operational constraints determine whether loads, drivers, carriers, routes, or transactions are enabled, restricted, priced differently, or rejected.

## Starting Hypothesis

A useful abstraction from platform software is:

**Expected ROI − Expected Risk → Decision**

In trucking, software may estimate factors such as:

- on-time probability
- cancellation or service-failure probability
- carrier or driver reliability
- safety risk
- fraud risk
- operating cost
- expected margin

Those estimates can influence allocation, pricing, restrictions, and access to economic opportunity.

## Research Model

```text
Real trucking operation
        ↓
Data
        ↓
Algorithm / decision logic
        ↓
Prediction
        ↓
Risk threshold
        ↓
Gate
        ↓
Economic outcome
```

## Core Research Questions

1. What exists in the trucking software ecosystem?
2. What resources, information, or capabilities are scarce?
3. What algorithms are used and what decisions do they influence?
4. Where does predicted risk create a gate?
5. What information is available before the gate is applied?
6. Where is uncertainty being treated as risk?
7. Can better information reduce uncertainty without increasing unacceptable risk?
8. Can reducing unnecessary gatekeeping create measurable economic value?

## Initial Domains

- load matching
- carrier selection
- driver assignment
- dispatch
- route planning
- pricing
- safety and compliance
- fraud prevention
- insurance and risk scoring
- fleet management
- transportation management systems

## Candidate Opportunity

The initial software opportunity is not to remove legitimate controls.

It is to investigate whether better information can distinguish **actual risk** from **uncertainty** well enough to safely enable activity that existing systems would otherwise restrict.

```text
Poor information
→ High uncertainty
→ High perceived risk
→ Gatekeeping

Better information
→ Lower uncertainty
→ Better risk estimation
→ Better allocation
→ More economically viable activity
```

## Research Before Product

This repository does not begin with a predetermined SaaS product.

A product hypothesis should emerge only after evidence identifies a recurring and economically meaningful problem where software can improve the decision boundary.

**Find the gate before building the product.**

## Evidence pipeline and current boundary

The FMCSA work proceeds through distinct, non-substitutable stages:

1. **Complete-frame infrastructure** — resumable acquisition and streaming audit code for a version-checked census frame. PR #19 reports a successful 4,490,646-row real-frame audit, although the large ignored evidence package is unavailable in this checkout and cannot be reverified here.
2. **Bounded ingestion cohort** — the deterministic first 100 rows of dataset `az4n-8mr2` under `dot_number ASC`. Run `python3 scripts/audit_fmcsa_census_bounded.py --expected-limit 100` to verify its identity, count, ordering, identifiers, digest, manifest, and explicitly non-random/non-representative/non-complete scope.
3. **Semantic binding** — authoritative meanings and coded values must be bound before a field can enter an eligibility rule. FMCSA's preserved Revision 8 Company Census dictionary now fully binds `status_code`, `carrier_operation`, and `safety_rating`. `docket1_status_code` remains unresolved for `P`, and `review_type` remains unresolved for `B`; inference remains prohibited for every field.
4. **Eligibility-rule freezing** — a deterministic cross-dataset candidate and a version-bound MOTUS complete frame now exist. `data/fmcsa/temporal-alignment-contract.json` preregisters the only authorized join: exact commit/artifact bindings, a fixed 24-hour dataset-version-marker ceiling, normalized USDOT equality, one-to-many authority behavior, and fail-closed missing data. The observed markers are 80,794 seconds apart. This checkout cannot execute the join because the required preserved Census evidence package is unavailable here. That environment limitation does not invalidate PR #19's historical real-frame audit and does not itself establish a terminal Issue #21 scientific determination.
5. **Prospective qualification/gate observation** — begins only after the instrument and eligibility rule are frozen. FMCSA state, platform-represented state, and the platform decision remain separate evidence classes.

Current checkout determination: `BOUNDED_COHORT_AUDIT_PASSED`; `SEMANTIC_BINDING_PARTIALLY_BOUND`; `CODEX_ENVIRONMENT_BLOCKED`; `ELIGIBILITY_RULE_NOT_FROZEN`; Issue #21 `UNRESOLVED`. These are pipeline and environment states, not evidence that any carrier is eligible or that any platform gate is valid or invalid.
