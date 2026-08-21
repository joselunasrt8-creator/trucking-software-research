# Collection protocol: 20 consecutive attempts

**Do not start collection until `qualification-attempt-v1` is reviewed and frozen.** The target is exactly 20 consecutive, eligible carrier-qualification attempts—not 20 selected outcomes.

1. Pre-register one start time, participating workflow, eligibility rule, exclusions, collector roster, and follow-up window. Assign sequential study IDs; exclude test/retry events under the pre-registered rule and log every exclusion separately.
2. Enroll every eligible attempt after the start until 20 are reached, regardless of carrier, decision, evidence completeness, or suspected error. Do not replace unfavorable or incomplete cases.
3. At T0, record attempt/decision timestamps and independently capture (a) authoritative state, (b) platform-represented state, (c) policy, and (d) the exact observed rule/predicate. Preserve source locator, retrieval time, artifact hash, and signal type. Use unknown/null fields rather than inference.
4. Freeze both T0 snapshots immediately. Redact direct identifiers in derived records while retaining access-controlled source artifacts under the study plan.
5. During the fixed follow-up window, append resolution evidence in observation order. Never alter T0 values. Record economic outcome only with its status, basis, time, and source; distinguish observed from estimated amounts.
6. Two reviewers independently adjudicate against the documented definitions. Resolve disagreement explicitly. `CONFIRMED_FALSE_GATE` requires authoritative evidence that the intended, applicable predicate was already satisfied at T0; otherwise use candidate or `INDETERMINATE` as warranted.
7. Validate each record, reconcile the enrollment/exclusion log to 20 consecutive attempts, freeze the cohort, and only then summarize counts and outcomes. Report missingness and indeterminate cases; do not silently drop them.

No scores, recommendations, or automated production decisions are produced by this protocol.
