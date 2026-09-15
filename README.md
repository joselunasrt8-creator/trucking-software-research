# Trucking Software Research

## Governing Question

**Where, if anywhere, does trucking software use predictions, risk estimates, constraints, or incomplete information in ways that materially govern economic opportunity?**

## Purpose

This repository studies trucking as a software-mediated economic system before attempting to build software for it.

The objective is to identify and empirically test consequential decision boundaries: places where software, data, rules, predictions, or operational constraints affect whether loads, drivers, carriers, routes, or transactions are enabled, restricted, priced differently, prioritized, or rejected.

The repository does not assume that such boundaries are primarily algorithmic, unfair, inefficient, or commercially addressable. Those are hypotheses to test.

## Starting Hypothesis

One candidate abstraction is:

```text
Expected return − expected risk → decision
```

Software may use or expose factors such as:

- on-time probability;
- cancellation or service-failure probability;
- carrier or driver reliability;
- safety and compliance state;
- fraud risk;
- operating cost;
- expected margin; and
- operational constraints.

But the existence, implementation, weighting, and causal importance of any such factor must be established from evidence for the specific system under study. A plausible decision model is not evidence that a platform actually uses that model.

## Candidate Research Model

```text
Observed system state
        ↓
Available information
        ↓
Decision mechanism
        ↓
Observed decision
        ↓
Economic outcome
```

Prediction, risk thresholds, or explicit gates may exist inside the decision mechanism, but they should not be inserted into the causal chain unless evidence supports them.

This distinction matters because a restriction can arise from many mechanisms: law, policy, capacity, contract, deterministic rules, market conditions, missing information, human judgment, model output, or combinations of these.

## Core Research Questions

1. What software-mediated decisions exist in the trucking ecosystem?
2. Which of those decisions materially affect economic opportunity?
3. What information is available before each consequential decision?
4. What mechanism actually produces the decision?
5. Where are prediction or risk estimates demonstrably involved?
6. Where are deterministic eligibility, legal, contractual, capacity, or operational constraints sufficient to explain the outcome?
7. Where does missing or uncertain information change the decision, if anywhere?
8. Can better information change a consequential decision without increasing unacceptable risk or violating legitimate constraints?
9. Does changing that decision boundary produce measurable economic value?
10. Does a proposed software intervention outperform the existing process or a strong simpler baseline?

## Candidate Domains

Potential study areas include:

- load matching;
- carrier selection;
- driver assignment;
- dispatch;
- route planning;
- pricing;
- safety and compliance;
- fraud prevention;
- insurance and risk scoring;
- fleet management; and
- transportation management systems.

Listing a domain does not establish that it contains the hypothesized mechanism or an addressable opportunity.

## Candidate Opportunity Hypothesis

One hypothesis is that some systems may treat incomplete information conservatively, and that better information could improve a decision without weakening legitimate controls.

```text
Incomplete information
        ↓ possible effect
Uncertainty
        ↓ possible effect
Conservative decision

Better information
        ↓ possible effect
Lower uncertainty
        ↓ possible effect
Different decision
        ↓
Measured outcome
```

Every arrow is empirical. Better information may have no effect, may reveal higher risk, may confirm the existing restriction, or may be economically irrelevant.

The objective is therefore **not** to reduce gatekeeping by default. It is to determine whether a specific consequential decision is poorly informed and whether improving information changes outcomes enough to matter.

## Research Before Product

This repository does not begin with a predetermined SaaS product or a predetermined conclusion that trucking software contains an exploitable decision boundary.

A product hypothesis should emerge only after evidence identifies a recurring, consequential, and economically meaningful problem where an intervention improves the outcome relative to a strong baseline.

A useful discipline is:

> **Find and verify the decision mechanism before designing the product.**

## FMCSA evidence program and current boundary

The current FMCSA work is a specific empirical program inside the broader repository. Its pipeline state must not be generalized into claims about the trucking industry or commercial software platforms.

It proceeds through distinct, non-substitutable stages:

1. **Complete-frame infrastructure** — acquisition/audit tooling and historical evidence exist, but the exact complete Census object required for the current eligible-frame execution is not presently available as a bound, replayable source artifact in the working evidence state. Historical claims of a complete frame must not be used to bypass current source-identity requirements.
2. **Bounded ingestion cohort** — the deterministic first 100 rows of dataset `az4n-8mr2` under `dot_number ASC` remain a bounded, non-random, non-representative cohort.
3. **Semantic binding** — authoritative meanings and coded values must be bound before a field can enter an eligibility rule. Inference remains prohibited for unresolved fields.
4. **Eligibility-rule freezing** — the rule may proceed only after its exact Census source identity, required semantics, and version-bound join inputs are legitimately available. Current determination: `BLOCKED_EXACT_CENSUS_VERSION_UNAVAILABLE`; `ELIGIBILITY_RULE_NOT_FROZEN`.
5. **Prospective qualification/gate observation** — begins only after the instrument and eligibility rule are frozen. FMCSA state, platform-represented state, and the platform decision remain separate evidence classes.

Current determination:

```text
BLOCKED_EXACT_CENSUS_VERSION_UNAVAILABLE
ELIGIBILITY_RULE_NOT_FROZEN
```

Prospective qualification observation has not started.

These are research pipeline states. They are not evidence that any carrier is eligible, that any platform gate exists, that a platform gate is valid or invalid, or that the proposed uncertainty/risk abstraction explains a real decision.

## Evidence hierarchy

Claims should remain separated by evidence class:

```text
Public / authoritative source state
        ≠
Platform-represented state
        ≠
Platform decision
        ≠
Decision mechanism
        ≠
Causal explanation
        ≠
Economic opportunity
        ≠
Product value
```

Observing that a carrier has a particular FMCSA state does not establish how a platform represents that state. Observing a platform decision does not establish why it occurred. Identifying a mechanism does not establish that changing it is safe, valuable, or commercially viable.

## Falsification boundary

The research must permit findings that weaken or terminate the starting hypothesis. Examples include:

- consequential decisions are adequately explained by deterministic legal, contractual, capacity, or operational constraints;
- prediction is not materially involved;
- uncertainty does not materially alter decisions;
- better information does not change outcomes;
- better information reveals that conservative decisions were justified;
- the apparent gate cannot be observed or attributed reliably;
- changing the decision increases unacceptable risk;
- the economic effect is too small to matter;
- a simpler intervention performs equally well; or
- no recurring software opportunity is found.

Any of these is a legitimate result.

## Relationship to Continufy

Trucking Software Research is a domain research repository. It may use Continufy research, methodology, structural, cognition, or governance components when a specific experiment justifies them, but ecosystem membership does not make those dependencies mandatory.

```text
Research relationship ≠ runtime dependency
Methodological fit ≠ causal proof
Governance capability ≠ evidence of market need
Internal architecture ≠ trucking-domain truth
```

The trucking domain should be allowed to falsify Continufy abstractions rather than being forced to instantiate them.

## Current objective

The immediate objective is to preserve the integrity of the FMCSA evidence boundary while determining whether a legitimately observable platform decision can eventually be connected to an identified decision mechanism.

Do not bypass unavailable source identity, infer unresolved semantics, convert bounded cohorts into population claims, or build product architecture to compensate for missing empirical evidence.

The strongest useful result may be a verified opportunity. It may also be a narrower model, a negative finding, or evidence that this research direction should stop.
