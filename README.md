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

1. **Complete-frame infrastructure** — acquisition/audit tooling and historical evidence exist, but the exact complete Census object required for the current eligible-frame execution is not presently available as a bound, replayable source artifact in the working evidence state. Historical claims of a complete frame must not be used to bypass current source-identity requirements.
2. **Bounded ingestion cohort** — the deterministic first 100 rows of dataset `az4n-8mr2` under `dot_number ASC` remain a bounded, non-random, non-representative cohort.
3. **Semantic binding** — authoritative meanings and coded values must be bound before a field can enter an eligibility rule. Inference remains prohibited for unresolved fields.
4. **Eligibility-rule freezing** — the rule may proceed only after its exact Census source identity, required semantics, and version-bound join inputs are legitimately available. Current determination: `BLOCKED_EXACT_CENSUS_VERSION_UNAVAILABLE`; `ELIGIBILITY_RULE_NOT_FROZEN`.
5. **Prospective qualification/gate observation** — begins only after the instrument and eligibility rule are frozen. FMCSA state, platform-represented state, and the platform decision remain separate evidence classes.

Current determination: `BLOCKED_EXACT_CENSUS_VERSION_UNAVAILABLE`; `ELIGIBILITY_RULE_NOT_FROZEN`; prospective qualification observation has not started. These are pipeline states, not evidence that any carrier is eligible or that any platform gate is valid or invalid.
