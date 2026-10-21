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

## Emerging Field-Learning Track: Specialized-Load Safety

A separate, exploratory track will investigate whether pre-trip planning for step-deck, RGN/lowboy, and permitted oversize loads contains recurring information gaps that software could help qualified personnel identify.

Potential areas to investigate include:

- load and trailer dimensional compatibility
- cargo weight, axle-distribution information, and equipment ratings
- securement documentation and working-load limits
- permit, escort, jurisdiction, and route-restriction checks
- conflicts, missing information, stale sources, and unresolved assumptions
- the cost of preventable planning errors, delays, and rework

This is a **product hypothesis, not a validated product or proven market opportunity**. Field observations must be lawful, safe, and authorized. Do not record or upload confidential employer, customer, driver, or shipment information without permission.

### Proposed development sequence

1. **Observe and document** recurring workflow problems using privacy-safe notes and synthetic examples.
2. **Plan the MVP** and define its scope, input schema, source requirements, uncertainty states, privacy controls, and validation criteria.
3. **Prototype a checklist-first analyzer** that shows evidence, flags missing or conflicting information, and routes unresolved items to qualified human review.
4. **Validate** with synthetic cases first, then authorized and redacted examples reviewed by qualified personnel.
5. **Decide based on evidence** whether a limited pilot or further development is justified.

The tool must not autonomously certify a load as safe, replace a physical inspection, authorize dispatch, or override driver, carrier, permit, or qualified safety decisions. Unknown or stale critical information must never be treated as a pass.

### Working issues

- [#35 — Anchor: Specialized trucking transition, field learning, economics, and software experiment](https://github.com/joselunasrt8-creator/trucking-software-research/issues/35)
- [#37 — Plan the MVP architecture and phased roadmap](https://github.com/joselunasrt8-creator/trucking-software-research/issues/37)
- [#36 — Design a human-reviewed pre-trip load safety analyzer](https://github.com/joselunasrt8-creator/trucking-software-research/issues/36)
- [#33 — Specialized-load feasibility checklist](https://github.com/joselunasrt8-creator/trucking-software-research/issues/33)
- [#32 — Field-observation protocol for step-deck / RGN / oversize workflows](https://github.com/joselunasrt8-creator/trucking-software-research/issues/32)

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
