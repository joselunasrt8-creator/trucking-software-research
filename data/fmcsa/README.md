# FMCSA Motor Carrier Census empirical boundary

The intended input is `data/raw/fmcsa/motor-carrier-census-10000.json` from the
U.S. Department of Transportation / Federal Motor Carrier Safety
Administration Socrata dataset `az4n-8mr2` (“Company Census File”). The raw
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
SHA-256. Acquisition time is the local UTC completion time recorded by the
acquisition script and is not confused with a publisher timestamp.

## Authoritative source references

Use the following first-party / federal catalog resources for source identity,
field definitions, and future reproducible acquisition work:

- Company Census File catalog record:
  https://catalog.data.gov/dataset/company-census-file
- Exact Socrata dataset identifier and machine-readable column definitions:
  https://data.transportation.gov/api/views/az4n-8mr2/columns.json
- Current JSON download endpoint exposed by the federal catalog:
  https://data.transportation.gov/api/v3/views/az4n-8mr2/query.json?accessType=DOWNLOAD
- FMCSA Dataset Description and Data Definitions — Select Datasets:
  https://data.transportation.gov/api/views/wahn-z3rq/files/6b2991b6-05c6-4745-a1d8-a1595f34b021?download=true&filename=FMCSA+Dataset+Description+and+Data+Definitions+-+Select+Datasets.pdf
- Broader Motor Carrier Registrations — Census Files catalog record:
  https://catalog.data.gov/dataset/motor-carrier-registrations-census-files

The Company Census File catalog describes the dataset as containing active,
inactive, and pending FMCSA entities and identifies USDOT number as the unique
entity identifier. Its JSON distribution explicitly links the machine-readable
`columns.json` definition for dataset `az4n-8mr2`.

The separate FMCSA data-definitions PDF covers selected FMCSA datasets,
including carrier/authority/insurance definitions. It must not be assumed to be
identical to the `az4n-8mr2` Company Census schema without an explicit field
mapping.

## Documentation comparison boundary

The repository now records authoritative external documentation references, but
it does not yet contain a frozen/versioned local copy or field-by-field mapping
for the exact acquisition snapshot. Therefore a documented-present/absent
comparison must still not be silently inferred from names alone.

Until the exact `az4n-8mr2` column definition is acquired, version-bound, and
mapped to the observed raw snapshot, the generated audit may remain
`not_assessable`. API labels or guessed meanings are not substitutes for that
mapping.

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

Keep the raw response local and gitignored. It is public and reproducibly
queried; Git LFS adds operational dependency without a stated need, and direct
Git storage creates repository history churn. Preserve exact bytes only when a
research snapshot is necessary; then use immutable object storage with the
committed digest/manifest rather than treating an API response as source code.

## Highest-information-gain next step

Acquire and version the exact `az4n-8mr2` machine-readable column definition,
then obtain a deterministically ordered complete eligible frame or immutable
snapshot. Bind both to digests before running the audit and preregistering the
sample. This resolves field semantics and selection bias before collecting
broker-rule and observed-decision evidence.
