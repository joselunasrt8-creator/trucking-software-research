# FMCSA Company Census empirical boundary (Issue #6)

## Current execution status

The authoritative hosts were unreachable from the 2026-08-22 implementation
environment (the proxy returned HTTP 403). No live schema, complete frame,
manifest, or eligible-frame counts are committed or claimed. Current status is:

```text
SCHEMA_NOT_BOUND
COMPLETE_FRAME_BLOCKED
```

The code path is fixture-tested, but fixture values are not empirical results.
The bounded live attempt is recorded in `execution-status.json`.

## Exact source identities and acquisition contract

- Dataset: **Company Census File**, Socrata ID `az4n-8mr2`, U.S. DOT / FMCSA.
- Schema: `https://data.transportation.gov/api/views/az4n-8mr2/columns.json`.
- Dataset metadata/version check:
  `https://data.transportation.gov/api/views/az4n-8mr2`.
- Rows: `https://data.transportation.gov/resource/az4n-8mr2.json`.
- Query contract: `$order=dot_number ASC` with deterministic `$limit`/`$offset`
  pages. `dot_number` is the stable ordering key. Missing or duplicate keys fail
  closed rather than invoking an undocumented tie-break or deduplication rule.

Run `python scripts/acquire_fmcsa_census.py`. The acquirer obtains the official
column array and preserves its source, retrieval time, canonical SHA-256 digest,
field names, labels, descriptions, and types. A missing official description is
explicitly unresolved; names and labels are never promoted into definitions.

It reads `rowsUpdatedAt` before pagination and again after the short (possibly
empty) terminal page. A change, absent version marker, malformed response,
unstable ordering, missing `dot_number`, or duplicate `dot_number` produces
`COMPLETE_FRAME_BLOCKED` and no output files. Transport failures, timeouts, HTTP
429, and HTTP 5xx receive three retries after 1, 2, and 4 seconds. Other HTTP
errors are not retried. Page provenance records URL, offset, requested limit,
row count, retrieval time, and digest.

On success, atomic writes produce the ignored raw JSON file, the official schema
binding, and `data/derived/fmcsa/complete-frame-manifest.json`. The manifest
records dataset and schema identity, start/completion times, exact query,
ordering, pagination, retry and termination contracts, page/row counts, raw
content digest, duplicate/missing counts, every page's provenance, and the
limitation that `rowsUpdatedAt` is a stability check rather than an immutable
snapshot selector. `python scripts/audit_fmcsa_census.py` rechecks the frozen
bytes, count, digest, and identifier counts.

Raw responses, live schema bindings, manifests, and eligible frames remain
gitignored because they are execution outputs, not source code.

## Eligible-carrier field boundary and transformation freeze

The preregistered target population remains **active interstate for-hire
property carriers as of a fixed reference date**. Issue #6 does not authorize
guessing which `az4n-8mr2` fields or code values establish active, interstate,
for-hire, or property status. Because the authoritative column definitions
could not be retrieved, none of those predicates is currently bound and the
complete-frame → eligible-frame construction rule is **not frozen**.

| field | authoritative definition | intended research use | observability limitation | disposition |
|---|---|---|---|---|
| `dot_number` | unresolved until official schema retrieval | stable carrier identity and ordering | does not establish eligibility | required for complete-frame integrity |
| active-status field | unresolved; field not selected | active predicate at the reference date | census state may not equal current authority | excluded until bound |
| operation field | unresolved; field not selected | interstate predicate | codes must not be inferred | excluded until bound |
| for-hire/property field(s) | unresolved; fields not selected | for-hire property predicate | may require another authoritative FMCSA source | excluded until bound |
| address/state fields | unresolved; fields not selected | descriptive/stratification use only | carrier state is not platform-represented state | optional only after binding |

Missing eligibility inputs will be excluded without imputation once definitions
are bound. Ambiguous duplicate identifiers will be rejected, not selected.
Before any qualification outcome is inspected, a later bounded execution must
freeze the reference date, exact authoritative field definitions and code
values, inclusion/exclusion predicates, missing-data behavior, deterministic
logic, and then record the eligible row count and canonical digest. That is the
next empirical step; it is not performed here.

FMCSA carrier state **does not equal** platform-represented state, a broker rule,
or a qualification decision. This work collects none of those other evidence
classes and tests no false-gate hypothesis.
