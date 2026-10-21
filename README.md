# Trucking Software Research

## Focus

Researching how trucking software uses data, algorithms, risk, and operational constraints to support safer, better-informed trucking decisions.

The current applied focus is **pre-trip planning for step-deck, RGN/lowboy, and permitted oversize loads**. The research asks whether software can help qualified personnel identify missing, conflicting, or outdated information before a load moves.

**Current stage:** Field learning and research. The proposed analyzer is a hypothesis, not a validated product.

## Governing question

**Can software make specialized-load planning information clearer and easier to verify without replacing professional judgment or safety controls?**

## Problem hypothesis

Specialized-load planning can involve information spread across equipment specifications, cargo measurements, securement documentation, permits, escort requirements, jurisdiction rules, and route restrictions. Missing or conflicting details may lead to delays, rework, or unsafe assumptions.

The research will test whether a checklist-first tool can surface those issues early and provide traceable evidence for human review.

This is a hypothesis to investigate, not an assertion that the problem is widespread or that a software solution will necessarily improve outcomes.

## Candidate workflow

```text
Load and equipment details
        ↓
Required documents and authoritative sources
        ↓
Compatibility and constraint checks
        ↓
Missing / conflicting / stale information flags
        ↓
Evidence and uncertainty summary
        ↓
Qualified human review
        ↓
Decision remains with responsible personnel
```

## Initial scope

Investigate whether a human-reviewed analyzer can help check and organize:

- cargo dimensions against trailer dimensions and configuration
- cargo weight, axle-distribution information, and equipment ratings
- securement plans, documentation, and working-load limits
- permit requirements by jurisdiction
- escort requirements and applicable restrictions
- route restrictions and known clearance constraints
- missing, conflicting, outdated, or unverified information
- unresolved questions that must be referred to qualified personnel

The tool should show the source, timestamp, and limitations of information where available. It should distinguish a verified check from an unresolved or unavailable check.

## Safety boundaries

The analyzer must not:

- autonomously certify a load as safe or legal
- replace physical inspection or required measurements
- authorize dispatch or override the driver, carrier, permit authority, or qualified safety personnel
- treat unknown, conflicting, or stale critical information as a pass
- present an inference as an authoritative rule
- imply that a checklist can capture every real-world hazard

Safety-critical decisions remain with the responsible qualified people and applicable authorities.

## Validation plan

1. **Observe:** Document recurring planning questions using lawful, authorized, privacy-safe notes.
2. **Define:** Specify the intended users, workflow, inputs, evidence requirements, uncertainty states, and explicit non-goals.
3. **Prototype:** Build a checklist-first workflow using synthetic cases.
4. **Test:** Evaluate missing data, conflicting measurements, stale sources, invalid assumptions, and clear stop/escalation cases.
5. **Review:** Have qualified personnel assess the outputs against authoritative documentation and real workflow needs.
6. **Decide:** Continue, revise, or stop based on recorded findings.

Do not record or upload confidential employer, customer, driver, or shipment information without permission. Use redacted, authorized examples for any testing beyond synthetic cases.

## What would validate the hypothesis?

Evidence should establish:

- which planning tasks repeatedly create confusion or rework
- which information sources are authoritative for each check
- whether the tool reliably identifies missing and conflicting inputs
- whether outputs are understandable and useful to qualified reviewers
- how often the tool produces false reassurance or misses a critical issue
- whether the tool reduces avoidable rework without encouraging unsafe reliance

A successful demo alone is not validation. Any prototype must be evaluated for failure cases and limitations before use in operational settings.

## Working issues

- [#35 — Anchor: Specialized trucking transition, field learning, and software experiment](https://github.com/joselunasrt8-creator/trucking-software-research/issues/35)
- [#37 — Plan the MVP architecture and phased roadmap](https://github.com/joselunasrt8-creator/trucking-software-research/issues/37)
- [#36 — Design a human-reviewed pre-trip load safety analyzer](https://github.com/joselunasrt8-creator/trucking-software-research/issues/36)
- [#33 — Specialized-load feasibility checklist](https://github.com/joselunasrt8-creator/trucking-software-research/issues/33)
- [#32 — Field-observation protocol for step-deck / RGN / oversize workflows](https://github.com/joselunasrt8-creator/trucking-software-research/issues/32)

## Separate research: carrier qualification evidence

The repository also contains an earlier empirical research track examining carrier qualification and platform decision gates. It is separate from the specialized-load safety work and remains blocked until the exact, version-bound FMCSA Company Census source artifact and required field semantics are available.

Current determination: `BLOCKED_EXACT_CENSUS_VERSION_UNAVAILABLE`; `ELIGIBILITY_RULE_NOT_FROZEN`. Prospective qualification observation has not started. These pipeline states do not establish whether any carrier is eligible or whether a platform decision is valid.

See [Issue #21](https://github.com/joselunasrt8-creator/trucking-software-research/issues/21), [Issue #23](https://github.com/joselunasrt8-creator/trucking-software-research/issues/23), and [Issue #25](https://github.com/joselunasrt8-creator/trucking-software-research/issues/25) for that workstream's evidence requirements.

## Research before product

The immediate priority is to understand the workflow, identify the most consequential information gaps, and test whether a human-reviewed tool can address them safely. Do not expand the scope or build around assumptions before field evidence supports the next step.

**Make uncertainty visible. Keep safety decisions with qualified people.**
