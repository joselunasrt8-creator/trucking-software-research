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
`COMPLETE_FRAME_BLOCKED` and does not replace any published output. Transient
URL/socket failures, timeouts and resets, `http.client.IncompleteRead`,
plausibly transient SSL read failures, HTTP 429, and HTTP 5xx receive three
retries after 1, 2, and 4 seconds. Certificate-verification failures and other
HTTP errors are not retried. A response-read failure occurs before JSON parsing,
so a partial JSON page is never accepted. Page provenance records URL, offset,
requested limit, row count, retrieval time, and digest.

Progress is committed after each complete page. The raw prefix is first
canonically serialized, flushed, and `fsync`ed; only then is an integrity-sealed
checkpoint atomically replaced and its directory `fsync`ed. The checkpoint
preserves the exact next offset, cumulative row count, prior `dot_number`, raw
prefix byte length and SHA-256 digest, schema binding, acquisition start time,
and all prior page provenance. It is bound to dataset/version, query and strict
ordering contracts, page size, serialization/schema identities, and the
resolved output paths. Re-running the same command resumes automatically. A
changed `rowsUpdatedAt`, schema, page size, order/query contract, output identity,
malformed checkpoint, missing partial file, or prefix digest mismatch fails
closed. Bytes written after the last checkpoint are verified as outside the
committed prefix and truncated before the exact next page is requested.

On success, atomic writes produce the ignored raw JSON file, the official schema
binding, and `data/derived/fmcsa/complete-frame-manifest.json`. The manifest
records dataset and schema identity, start/completion times, exact query,
ordering, pagination, retry and termination contracts, page/row counts, raw
content digest, duplicate/missing counts, every page's provenance, and the
limitation that `rowsUpdatedAt` is a stability check rather than an immutable
snapshot selector. `python scripts/audit_fmcsa_census.py` rechecks the frozen
frame bytes, count, digest, identifier counts, schema artifact digest, and the
dataset/schema source identities. A missing, malformed, or altered schema fails
closed. The manifest remains the final publication commit marker. Only after it
is published successfully are the checkpoint and partial-work names removed.

Raw responses, live schema bindings, manifests, and eligible frames remain
gitignored because they are execution outputs, not source code.

The complete-frame audit has the same bounded-resource invariant as acquisition:
its memory consumption must not scale approximately with complete-frame size.
It incrementally hashes and frames the top-level JSON array, retaining only one
record at a time, and stores exact `dot_number` uniqueness state in a temporary
on-disk SQLite B-tree with a bounded cache. The temporary state is removed after
either success or failure. Malformed arrays and objects, non-object records,
records larger than the fixed 64 MiB corruption guard, digest/count differences,
and provenance inconsistencies continue to fail closed as
`COMPLETE_FRAME_BLOCKED`; no probabilistic duplicate check is used.

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
