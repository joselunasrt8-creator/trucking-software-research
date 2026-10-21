# Trucking Software Research

## Overview

Researching how trucking software uses algorithms, risk, constraints, and prediction to govern economic opportunity.

This repository studies trucking as a software system before attempting to build software for it. It investigates how data and decision logic influence which loads, drivers, carriers, routes, and transactions are enabled, restricted, priced differently, or rejected.

**Current stage:** Research and evidence development. No product or market opportunity described here should be treated as validated unless supporting evidence is documented.

## Governing question

**Where does trucking software use predictions, risk, and constraints to govern economic opportunity?**

## Research model

The working conceptual model is:

```text
Real trucking operation
        ↓
Data and observations
        ↓
Algorithm / decision logic
        ↓
Prediction or classification
        ↓
Threshold or constraint
        ↓
Decision gate
        ↓
Operational and economic outcome
```

A useful initial heuristic is:

**Expected return, considered alongside expected risk and constraints → decision**

This is a research heuristic, not a calibrated mathematical formula. Any quantitative model must define its variables, units, assumptions, and validation method before being used to support conclusions.

Software may estimate or represent factors such as:

- on-time probability
- cancellation or service-failure probability
- carrier or driver reliability
- safety and compliance risk
- fraud risk
- operating cost
- expected margin

These estimates can influence allocation, pricing, restrictions, and access to economic opportunity. The repository distinguishes documented system behavior from hypotheses about how a system might work.

## Core research questions

1. What exists in the trucking software ecosystem?
2. What resources, information, or capabilities are scarce?
3. What algorithms are used, and which decisions do they influence?
4. Where does predicted risk create a decision gate?
5. What information is available before the gate is applied?
6. Where is uncertainty being treated as risk?
7. Can better information reduce uncertainty without increasing unacceptable risk?
8. Can reducing unnecessary gatekeeping create measurable economic value?

## Research domains

- load matching and carrier selection
- driver assignment and dispatch
- route planning and restrictions
- pricing and unit economics
- safety and compliance
- fraud prevention
- insurance and risk scoring
- fleet and transportation management systems

## Research opportunity hypothesis

The initial opportunity is not to remove legitimate controls. It is to investigate whether better information can distinguish **actual risk** from **uncertainty** well enough to safely enable activity that existing systems might otherwise restrict.

```text
Poor or incomplete information
→ Higher uncertainty
→ Potentially distorted risk estimate
→ Decision gate

Better, validated information
→ Better-supported risk estimate
→ Better-informed decision
→ Potentially improved allocation and economics
```

This relationship is a hypothesis to test, not a guaranteed outcome. A model can also create harm if its data are incomplete, its assumptions are wrong, or its recommendations are treated as authoritative without validation.

## Active research tracks

### 1. Carrier qualification and decision-gate evidence

This track develops a reproducible evidence pipeline for studying carrier qualification and represented platform decisions. It separates authoritative carrier-state evidence, platform-represented state, and actual platform decisions. These evidence classes must not be conflated.

**Current status:** Blocked at the exact, version-bound FMCSA Company Census source artifact needed for eligible-frame construction. The eligibility rule is not frozen, and prospective qualification observation has not started. This is a research-pipeline status, not evidence that a carrier is eligible or that a platform gate is valid or invalid.

Key references:
- [Issue #21 — Freeze the eligible carrier frame](https://github.com/joselunasrt8-creator/trucking-software-research/issues/21)
- [Issue #23 — Bind the canonical empirical evidence package](https://github.com/joselunasrt8-creator/trucking-software-research/issues/23)
- [Issue #25 — Authorize and acquire a new FMCSA frame](https://github.com/joselunasrt8-creator/trucking-software-research/issues/25)

### 2. Specialized-load safety and pre-trip planning

This exploratory field-learning track investigates whether planning for step-deck, RGN/lowboy, and permitted oversize loads contains recurring information gaps that software could help qualified personnel identify.

Potential areas include:

- load and trailer dimensional compatibility
- cargo weight, axle-distribution information, and equipment ratings
- securement documentation and working-load limits
- permit, escort, jurisdiction, and route-restriction checks
- missing, conflicting, stale, or unresolved information
- preventable planning errors, delays, and rework

**Status:** Product hypothesis only. The problem frequency, buyer, willingness to pay, and measurable value have not yet been validated.

#### Proposed development sequence

1. **Observe:** Document recurring workflow problems using lawful, authorized, privacy-safe notes and synthetic examples.
2. **Plan:** Define MVP scope, inputs, source requirements, uncertainty states, privacy controls, and validation criteria.
3. **Prototype:** Build a checklist-first analyzer that presents evidence, flags missing or conflicting information, and routes unresolved items to qualified human review.
4. **Validate:** Start with synthetic cases, then use authorized and redacted examples reviewed by qualified personnel.
5. **Decide:** Continue, revise, pilot, or stop based on documented evidence.

The analyzer must not autonomously certify a load as safe, replace physical inspection, authorize dispatch, or override driver, carrier, permit, or qualified safety decisions. Unknown or stale critical information must never be treated as a pass.

#### Working issues

- [#35 — Anchor: Specialized trucking transition, field learning, economics, and software experiment](https://github.com/joselunasrt8-creator/trucking-software-research/issues/35)
- [#37 — Plan the MVP architecture and phased roadmap](https://github.com/joselunasrt8-creator/trucking-software-research/issues/37)
- [#36 — Design a human-reviewed pre-trip load safety analyzer](https://github.com/joselunasrt8-creator/trucking-software-research/issues/36)
- [#33 — Specialized-load feasibility checklist](https://github.com/joselunasrt8-creator/trucking-software-research/issues/33)
- [#32 — Field-observation protocol for step-deck / RGN / oversize workflows](https://github.com/joselunasrt8-creator/trucking-software-research/issues/32)

## Evidence pipeline: FMCSA carrier frame

The FMCSA work uses the Company Census dataset `az4n-8mr2`, as identified in the repository's source-specific research issues. Dataset identity alone does not establish that a particular downloaded artifact is complete, current, or verified.

The work proceeds through distinct stages:

1. **Complete-frame infrastructure:** Acquisition and audit tooling exist, but the exact complete Census object required for the current eligible-frame execution is not presently available as a bound, replayable source artifact in the working evidence state. Historical claims of a complete frame must not bypass current source-identity requirements.
2. **Bounded ingestion cohort:** The deterministic first 100 rows under `dot_number ASC` remain a bounded, non-random, non-representative cohort.
3. **Semantic binding:** Authoritative field meanings and coded values must be bound before a field can enter an eligibility rule. Inference is prohibited for unresolved fields.
4. **Eligibility-rule freezing:** The rule can proceed only after the exact Census source identity, required semantics, and version-bound join inputs are legitimately available.
5. **Prospective qualification observation:** Begins only after the instrument and eligibility rule are frozen. FMCSA state, platform-represented state, and platform decisions remain separate evidence classes.

**Current determination:** `BLOCKED_EXACT_CENSUS_VERSION_UNAVAILABLE`; `ELIGIBILITY_RULE_NOT_FROZEN`. Prospective qualification observation has not started.

These are pipeline states, not evidence that any carrier is eligible or that any platform gate is valid or invalid. See [Issue #21](https://github.com/joselunasrt8-creator/trucking-software-research/issues/21) for the current source and eligibility boundary.

## Evidence and governance standards

Across both tracks:

- Preserve source identity, provenance, retrieval time, and known limitations.
- Distinguish observations, assumptions, hypotheses, and validated findings.
- Record missingness and uncertainty explicitly; do not infer undocumented semantics.
- Do not claim representativeness from bounded or non-random cohorts.
- Use data only when access is lawful and authorized; minimize personal and confidential information.
- Do not treat data availability as proof of validity, representativeness, authority, or permission to act.
- Keep recommendations separate from execution and preserve human accountability for safety-critical decisions.

```text
Data ≠ Evidence
Evidence ≠ Validated Model
Validated Model ≠ Authority
Recommendation ≠ Execution
```

## Research before product

This repository does not begin with a predetermined SaaS product. A product hypothesis should emerge only after evidence identifies a recurring, economically meaningful problem where software can improve a decision without creating unacceptable risk.

**Find the gate before building the product.**
