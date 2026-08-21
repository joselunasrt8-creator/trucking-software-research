# `qualification-attempt-v1`

This is a research measurement instrument for a single carrier-qualification attempt. It is **not** a product, recommendation, score, or production decision contract. Freeze this version before collecting the prospective cohort.

## Causal record shape

`authoritative_state` → `platform_state` → `policy` + `rule` → `decision` → `later_evidence` → `economic_outcome` → `reviewer_assessments` → `adjudication`

The two T0 evidence sets are deliberately separate. Authoritative evidence describes what an identified authority said was true; platform evidence describes what the deciding interface represented. Neither is silently preferred or overwritten. `policy.policy_type` keeps regulation, broker policy, platform requirements, and risk signals distinct.

## Field dictionary

| Field | Meaning |
|---|---|
| `instrument_version` | Exact schema/instrument version; always `qualification-attempt-v1`. |
| `attempt_id` | Study-local pseudonymous identifier for one attempt. |
| `t0.attempted_at` | When qualification was actually attempted (T0). |
| `t0.captured_at` | When the researcher fixed the T0 snapshot. |
| `t0.collector_id` | Pseudonymous collector identifier. |
| `authoritative_state.snapshot_at` | Effective time of the authoritative snapshot used at T0. |
| `authoritative_state.evidence[]` | Facts obtained from regulators or another named authoritative source. |
| `platform_state.snapshot_at` | Effective time of the displayed/represented platform snapshot at T0. |
| `platform_state.evidence[]` | What the broker/platform represented, including stale or missing values. |
| `policy.policy_type` | `REGULATORY_REQUIREMENT`, `BROKER_POLICY`, `PLATFORM_REQUIREMENT`, or `RISK_SIGNAL`; do not conflate them. |
| `policy.owner/source/version` | Entity accountable for the policy, provenance of the observed text, and its version (null only when unavailable). |
| `rule.owner/source/version` | Entity accountable for the applied rule and the provenance/version observed at T0. |
| `rule.observability` | Whether the logic is exactly visible, partially visible, or unknown/proprietary. |
| `rule.predicate.expression/threshold/unit` | Exact predicate and cutoff where observed. Null for unknown proprietary logic; never reverse-engineer it into asserted fact. |
| `rule.predicate.t0_evaluation` | Researcher evaluation of the *intended observed predicate* at T0, with T0 evidence IDs. `UNKNOWN` when it cannot be evaluated. |
| `rule.signal_type` | `MEASURED_FACT`, `CALIBRATED_RISK`, `UNCERTAINTY_PROXY`, or `UNKNOWN_PROPRIETARY_SIGNAL`. |
| `decision.state` | Gate result: `ALLOW`, `DELAY`, `REVIEW`, or `REJECT`. |
| `decision.decided_at/actor/reason_observed` | Decision time, deciding party/system, and verbatim-or-close displayed reason (null if absent). |
| `later_evidence[]` | Append-only, sequenced observations after T0. Never edit either T0 evidence set to reflect these observations. |
| `economic_outcome` | Observed/estimated/missing monetary consequence, currency, amount, basis, time, and provenance. Nulls preserve missingness. |
| `reviewer_assessments[]` | At least two independent pre-reconciliation reviewer classifications, each with reviewer identity, time, rationale, and evidence references. These are retained even when reviewers disagree. |
| `adjudication.classification` | Final reconciled classification: `VALID_GATE`, `CANDIDATE_FALSE_GATE`, `CONFIRMED_FALSE_GATE`, or `INDETERMINATE`. |
| `adjudication.reconciliation_status` | `AGREEMENT` when independent reviewers agree; `DISAGREEMENT_RESOLVED` when a discrepancy is explicitly reconciled. |
| `adjudication.*` | Final resolution time, resolver identity, rationale, and evidence IDs supporting the reconciled classification. |

Every evidence item has an ID, named field, value, `as_of` time, capture time, provenance object, and signal type. Every provenance object records source class, stable locator, retrieval time, and a SHA-256 content hash when an artifact can be retained.

## Classification rules

- **VALID_GATE:** available evidence supports that the applicable intended predicate was not satisfied at T0.
- **CANDIDATE_FALSE_GATE:** a restrictive decision conflicts with available information, but T0 predicate satisfaction or rule applicability is not yet proven.
- **CONFIRMED_FALSE_GATE:** `DELAY`, `REVIEW`, or `REJECT`; the applicable intended predicate is known; and cited, authoritative T0 evidence proves it was already satisfied. Later correction alone is insufficient.
- **INDETERMINATE:** evidence, provenance, rule meaning, applicability, or timing is insufficient or contradictory. Preserve this state rather than guessing.

The schema enforces the core confirmed-false-gate precondition. `validate.py` additionally checks that cited predicate evidence IDs resolve specifically to the authoritative T0 snapshot, that later evidence is strictly sequenced and occurs after T0, and that independent reviewer assessments are preserved before final reconciliation.

## Independent review and reconciliation

Each record must contain at least two independent `reviewer_assessments`. Reviewers classify the case separately before seeing a reconciled result. The final `adjudication` is a distinct object: it records either agreement or explicit disagreement resolution and must not overwrite or replace the reviewer-level assessments.

## Append-only lifecycle

Create the record with fixed T0 snapshots. Add later evidence as new entries with monotonically increasing `sequence`; never delete/reorder entries or revise T0 to match later knowledge. A correction is another later entry. Reviewer assessments and final adjudication should also be retained as research lineage. The retained research log should preserve each prior record revision externally (for example, in version control or immutable storage).

## Validation

```bash
python -m unittest discover -s tests -v
python instruments/qualification-attempt-v1/validate.py instruments/qualification-attempt-v1/example.json
```
