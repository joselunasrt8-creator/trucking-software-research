# FMCSA Motor Carrier Census empirical boundary

The intended input is `data/raw/fmcsa/motor-carrier-census-10000.json` from the
U.S. Department of Transportation / Federal Motor Carrier Safety
Administration Socrata dataset `az4n-8mr2` (“Motor Carrier Census”). The raw
file is deliberately ignored. Recreate and audit it with:

```sh
python scripts/acquire_fmcsa_census.py
python scripts/audit_fmcsa_census.py
```

Acquisition is exactly `$limit=10000`; it has no `$order`, `$offset`, filter,
randomization, snapshot/version selector, or application token. A limit caps a
response; it does **not** establish probability sampling. The result must be
called an **ingestion/audit cohort**, never a random or representative sample.

The audit writes `data/derived/fmcsa/motor-carrier-census-10000-audit.json`,
which is the empirical schema, missingness, vocabulary, range, duplicate, and
anomaly record, and `provenance.json`, which binds the exact raw bytes by
SHA-256. Acquisition time is the local UTC completion time and is not confused
with a publisher timestamp.

## Documentation comparison boundary

No FMCSA Census README or data-definition artifact is present in this
repository. Therefore the required documented-present/absent comparison cannot
be silently inferred. The generated audit records this as `not_assessable` and
keeps observed fields separate. A versioned source data definition must be
added or cited before making that comparison; API labels or guessed meanings
are not substitutes.

## Preregistered cohort proposal (before looking at outcomes)

1. Freeze a dataset version/acquisition timestamp and its digest.
2. Define the target population as active interstate for-hire property carriers
   as of a fixed reference date, using only predeclared FMCSA authority/status,
   operation, and cargo predicates whose exact field definitions have been
   verified.
3. Exclude records missing the unique carrier identifier or fields required by
   those eligibility predicates; report every exclusion count and do not impute
   eligibility.
4. Deduplicate by `dot_number` using a rule fixed before analysis (prefer a
   documented record-update timestamp; otherwise reject ambiguous duplicates).
5. Draw a seeded simple-random or state-stratified sample from the complete
   eligible frame, publish the seed and algorithm, and retain all selected
   carriers regardless of whether they look likely to confirm a false gate.
6. Keep hypothesis testing separate from this 10,000-row ingestion audit.

## Qualification evidence boundary

Exact classification depends on the observed schema and authoritative field
definitions. In general, census fields can support only dated **FMCSA carrier
state evidence** such as identity, registered address/state, operation/entity
classification, authority/status fields, fleet/driver counts, cargo flags, and
reported census dates when those fields are actually present and defined.

They only partially support predicates whose truth changes after the snapshot
or requires another FMCSA source: current authority, insurance/filing state,
safety fitness, inspection/crash history, or identity matching.

They do not observe broker/platform onboarding state, the platform's displayed
or internally represented carrier state, broker qualification rules, rule
versions, insurance limits and endorsements, lane/equipment availability,
fraud checks, performance history, prices, offers, application evidence, or an
actual accept/reject decision.

**FMCSA carrier state evidence ≠ broker/platform represented state ≠ broker
qualification rule ≠ observed qualification decision.** This source alone
cannot demonstrate a false gate.

## Storage recommendation

Keep the raw response local and gitignored. It is public, reproducibly queried,
and about 11 MB; Git LFS adds operational dependency without a stated need, and
direct Git storage creates repository history churn. Preserve exact bytes only
when a research snapshot is necessary; then use immutable object storage with
the committed digest/manifest rather than treating an API response as source
code.

## Highest-information-gain next step

Obtain and version the authoritative FMCSA/Socrata data definition and a
deterministically ordered complete eligible frame (or immutable snapshot), then
run the audit and preregister/draw the sample. This resolves field semantics and
selection bias before collecting broker-rule and observed-decision evidence.
