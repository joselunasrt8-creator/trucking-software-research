# Trucking Software Research

## Mission

Research how trucking software uses data, algorithms, predictions, risk signals, and operational constraints to shape decisions—and how those decisions can be examined, verified, and improved without weakening legitimate safety or compliance controls.

This repository combines **empirical research**, **evidence-pipeline tooling**, and **exploratory workflow research**. It is not committed to a single product or claim. Each workstream has its own evidence requirements, status, and stop/go criteria.

**Current stage:** Research and tooling development. Some data-pipeline scripts and tests exist; prospective field validation and the specialized-load analyzer remain incomplete. No broad product, safety, or market claim should be treated as validated without documented evidence.

## Core research question

**When trucking software makes or supports a decision, what facts, rules, predictions, and uncertainties drive that decision—and what evidence would show whether it is justified?**

## Research framework

```text
Operational reality
        ↓
Available evidence and data quality
        ↓
Rule, model, prediction, or constraint
        ↓
Decision / recommendation / review gate
        ↓
Operational outcome
        ↓
Evidence-based evaluation
```

The framework distinguishes:

- **Underlying state:** What is actually true in the operation.
- **Represented state:** What the system's available records say.
- **Rule or policy:** The documented requirement or decision condition.
- **Risk estimate:** A prediction or signal about a possible outcome.
- **Uncertainty:** What cannot be established from available evidence.
- **Decision:** What the system or responsible person does with that information.
- **Outcome:** What subsequently happens and what can be verified.

These categories must not be collapsed. A missing record is not automatically proof of a failed requirement; a prediction is not a fact; a tool recommendation is not authority to act.

## Research tracks

### 1. Carrier qualification and platform decision gates

**Question:** When a carrier is delayed, reviewed, or rejected during qualification, was the underlying requirement genuinely unsatisfied, or did missing, stale, conflicting, or misrepresented evidence prevent the system from establishing the true state?

This track studies the boundary between carrier state, represented evidence, qualification rules, and observed gate outcomes. It does not assume every rejection is wrong or infer proprietary scoring logic without evidence.

Current work includes:

- FMCSA Company Census acquisition and audit tooling
- source identity, schema semantics, and evidence provenance
- deterministic bounded-cohort handling
- eligibility-rule and evidence-package verification
- a proposed prospective qualification-attempt instrument
- classification of valid gates, candidate false gates, confirmed false gates, and indeterminate cases

**Status:** Tooling and research artifacts exist, but the exact version-bound Census source artifact and required semantic bindings remain gating dependencies for the current eligible-frame workflow. The eligibility rule is not frozen, and prospective qualification observation has not started. These limitations must remain visible; they do not establish whether any carrier or platform decision is valid.

Key references:
- [Issue #1 — Measure false gates in carrier qualification and load booking](https://github.com/joselunasrt8-creator/trucking-software-research/issues/1)
- [Issue #2 — Run prospective carrier qualification false-gate pilot](https://github.com/joselunasrt8-creator/trucking-software-research/issues/2)
- [Issue #21 — Freeze the eligible carrier frame](https://github.com/joselunasrt8-creator/trucking-software-research/issues/21)
- [Issue #23 — Bind the canonical empirical evidence package](https://github.com/joselunasrt8-creator/trucking-software-research/issues/23)
- [Issue #25 — Authorize and acquire a new FMCSA frame](https://github.com/joselunasrt8-creator/trucking-software-research/issues/25)

Implementation areas:
- [Scripts](https://github.com/joselunasrt8-creator/trucking-software-research/tree/main/scripts)
- [Tests](https://github.com/joselunasrt8-creator/trucking-software-research/tree/main/tests)
- [Qualification-attempt instrument](https://github.com/joselunasrt8-creator/trucking-software-research/tree/main/instruments/qualification-attempt-v1)

### 2. Specialized-load planning and safety information

**Question:** Can software help specialized-haul personnel find missing, conflicting, stale, or unverified planning information before a load moves—without replacing qualified judgment or safety controls?

The exploratory focus includes step-deck, RGN/lowboy, and permitted oversize workflows. Candidate information areas include:

- cargo and trailer dimensions and configuration
- weight, axle-distribution information, and equipment ratings
- securement plans, documentation, and working-load limits
- permit and escort requirements by jurisdiction
- route restrictions and known clearance constraints
- conflicting documents and unresolved planning questions

The research starts with observation and checklist-first methods, not an assumption that a full AI product is necessary. Existing checklists, experienced personnel, and current software may already solve some of these problems adequately.

**Status:** Hypothesis and planning stage. The frequency and importance of the problem, the specific gap in existing methods, user demand, and analyzer accuracy have not been validated.

Validation requires two separate forms of evidence:

1. **Need and workflow evidence:** recurring problems across independent workflows, clear users and decision points, documented current workarounds, and users willing to continue structured testing.
2. **Safety and performance evidence:** source-backed checks, synthetic failure cases, explicit uncertainty states, qualified review, and measurement of missed issues, unnecessary flags, and unresolved cases.

A demonstration or positive feedback alone is not validation. If current methods already work well or the problem is too rare to matter, narrow or stop the hypothesis.

Key references:
- [#35 — Anchor: Specialized trucking transition, field learning, and software experiment](https://github.com/joselunasrt8-creator/trucking-software-research/issues/35)
- [#37 — Plan the MVP architecture and phased roadmap](https://github.com/joselunasrt8-creator/trucking-software-research/issues/37)
- [#36 — Design a human-reviewed pre-trip load safety analyzer](https://github.com/joselunasrt8-creator/trucking-software-research/issues/36)
- [#33 — Specialized-load feasibility checklist](https://github.com/joselunasrt8-creator/trucking-software-research/issues/33)
- [#32 — Field-observation protocol](https://github.com/joselunasrt8-creator/trucking-software-research/issues/32)

#### Safety boundaries

Any analyzer remains decision support. It must not autonomously certify a load as safe or legal, replace physical inspection, authorize dispatch, or override the driver, carrier, permit authority, or qualified safety personnel. Unknown, conflicting, or stale critical information must never be treated as a pass. No confidential employer, customer, driver, or shipment information may be used without authorization.

### 3. Cross-cutting evidence and decision quality

Both tracks share methodological questions:

- What was known at the time of the decision?
- Which source establishes each fact, and how current is it?
- What is the governing rule, and is it applicable in this context?
- Is a conclusion based on a measured fact, a prediction, an assumption, or an unknown proprietary signal?
- What evidence would confirm, weaken, or falsify the claim?
- What should remain indeterminate or require human review?
- Can another researcher reproduce the result from the recorded evidence?

This is a shared method, not a claim that the two tracks are one product or that results from one can automatically validate the other.

## Evidence standards

Across the repository:

- Preserve source identity, provenance, retrieval time, version, and known limitations.
- Separate observations, interpretations, hypotheses, and validated findings.
- Record missingness and uncertainty explicitly.
- Do not claim representativeness from bounded or non-random cohorts.
- Do not infer undocumented field meanings or proprietary rules.
- Preserve contradictory evidence and negative results.
- Use data only when access is lawful and authorized; minimize personal and confidential information.
- Treat safety, compliance, fraud, and service outcomes as essential constraints, not optional afterthoughts.
- Keep recommendations separate from execution and preserve human accountability for safety-critical decisions.

```text
Data ≠ Evidence
Evidence ≠ Validation
Prediction ≠ Fact
Recommendation ≠ Authority
Unknown ≠ Pass
```

## Repository map

- `scripts/` — FMCSA acquisition, audit, and evidence-verification tooling
- `tests/` — automated tests for the current data-pipeline scripts and evidence checks
- `instruments/` — structured research instruments
- `data/` — data areas, with raw and derived artifacts separated
- `.github/workflows/` — repository automation and CI

Do not assume that the presence of a script, test, or directory proves the entire research pipeline is complete or that the underlying hypothesis is validated. Check the relevant issue and recorded evidence for current status.

## How progress is evaluated

A research track advances only when its own prerequisites are met:

1. Define a bounded question and unit of analysis.
2. Identify the authoritative evidence and the limits of access.
3. Specify classification rules before interpreting results.
4. Test scripts and instruments against edge cases.
5. Collect only authorized evidence with provenance.
6. Record results, uncertainty, contradictions, and failures.
7. Decide whether to continue, revise, pause, or stop.

The repository may legitimately conclude that a hypothesis is unsupported, a pipeline is blocked, or no new product is warranted.

## Research before product

The goal is to understand real workflows and decision boundaries before committing to a product direction. Build only when the evidence identifies a recurring problem, an actionable and legitimate intervention point, and a testable path to improvement.

**Make the decision process inspectable. Preserve uncertainty. Keep safety authority with qualified people.**
