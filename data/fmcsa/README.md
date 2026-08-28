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

### Issue #21 bounded re-evaluation (2026-08-28)

Issue #21 cannot legitimately freeze an eligible frame from the repository-owned
evidence available in this checkout. The ignored complete-frame bytes,
acquisition manifest, authoritative schema binding, and successful real-frame
audit artifact are absent. Consequently, the source content digest, row count,
schema digests, acquisition/retrieval window, and real-frame audit result cannot
be verified or bound. Merge commits for PRs #18 and #19 prove that the streaming
audit implementation was reviewed and merged; they do not substitute for its
empirical output.

Issue #6 has therefore been re-evaluated from preserved evidence and remains
`COMPLETE_FRAME_BLOCKED`, not `COMPLETE_FRAME_READY_WITH_LIMITATIONS`. The
fixture-tested acquisition and audit paths demonstrate executable validation
logic only. They do not establish a canonical acquired frame or authoritative
eligibility semantics.

No eligibility predicate, transformation, derived eligible-frame artifact, or
sampling operation was created. Doing so would require either manufacturing
missing source evidence or inferring undocumented meanings for the active,
interstate, for-hire, and property-carrier fields. Both are outside the research
boundary. Once the exact ignored artifacts are restored, Issue #21 must first
verify them with `python scripts/audit_fmcsa_census.py`, then bind every
eligibility field to its preserved authoritative definition and code values
before inspecting qualification outcomes or implementing the transformation.

The canonical Issue #21 determination for this evidence state is:

```text
ELIGIBLE_FRAME_BLOCKED
```

### Issue #23 portable evidence package

`evidence-package.json` is the repository-owned, machine-readable inventory for
the canonical empirical prerequisites. It separates a historical claim from
possession, retrieval, and successful verification; records each required
artifact's identity, provenance, location, retrieval and verification method,
status, and blocker; and binds the unresolved authoritative field semantics.

A search of tracked history and the checkout found no complete-frame bytes,
produced acquisition manifest, produced schema binding, real-frame audit output,
Git LFS configuration, release/storage binding, exact artifact digest, byte-size
record, or row-count record. The ignored output paths are local conventions, not
retrieval references. The official live schema and row endpoints are legitimate
sources for a new acquisition only: without a historical digest or immutable
snapshot selector, querying them cannot recover or prove the prior object.

Run the deterministic readiness check from a fresh checkout:

```bash
python scripts/verify_fmcsa_evidence_package.py
```

Exit status `2` and `CANONICAL_EVIDENCE_PACKAGE_BLOCKED` are the expected result
while mandatory artifacts or identities remain absent. A file appearing at an
ignored path is not accepted on presence alone: its expected digest and byte
size must already be bound, and the canonical auditor must validate the frame,
manifest, schema identities, row count, ordering, and relationships. Unknown or
mismatched identities fail closed. No reacquired live response may overwrite or
inherit the missing historical identity.

The Issue #23 determination is:

```text
CANONICAL_EVIDENCE_PACKAGE_BLOCKED
```

### Historical recovery investigation

`recovery-report.json` records each recovery lead, access attempt, artifact-level
classification, blocker type, and evidence reference. The local checkout, every
available commit/ref, unreachable Git objects, Git/LFS configuration, workflow
history, ignored paths, scripts, documentation, and storage/environment-variable
references yielded no historical digest, byte size, row count, artifact locator,
release asset, workflow artifact ID, object key, or repository LFS object.

The raw frame, manifest, and audit are therefore
`IRRECOVERABLE_FROM_AVAILABLE_EVIDENCE`: their ignored filesystem names are
generation destinations, not retrieval locations. The authoritative columns
endpoint is a legitimate path for a current schema object, but not for the
unidentified historical capture. Access to that endpoint, the GitHub project,
PRs #18/#19, and the releases surface was blocked by the execution environment's
CONNECT proxy before any response content was received.

The aggregate historical state is consequently
`HISTORICAL_PACKAGE_ACCESS_BLOCKED`, not `HISTORICAL_PACKAGE_IRRECOVERABLE`.
Legitimate external evidence surfaces were not exhaustively inspectable. No file
was recovered, no identity became verified, and the canonical package remains
blocked.

`reacquisition-requirement.json` preserves the governed transition and the
requirements for a distinct new empirical object. Its status is
`NOT_AUTHORIZED_PENDING_RECOVERY_ACCESS`: an access-capable recovery pass and an
explicit authorizing issue must precede any live acquisition. No reacquisition
was performed in this investigation.

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
It incrementally hashes and decodes the top-level JSON array in fixed-size
chunks, retaining at most a bounded input buffer and one record. Acquisition's
authoritative contract orders rows by numeric `dot_number` ascending and rejects
missing, duplicate, or descending identifiers before publication, including at
page and resume boundaries. The audit validates the manifest's exact ordered
query, independently revalidates numeric order, and counts equal adjacent
identifiers exactly. Any descending identifier fails closed. Because every equal
value in a nondecreasing sequence is adjacent to its prior occurrence, this is
scientifically equivalent to a global uniqueness index while requiring only the
prior identifier as state; no probabilistic duplicate check is used.

New manifests publish the strict `ordering_contract` already integrity-bound in
acquisition checkpoints. The preserved complete-frame manifest predates that
explicit field, but records the same exact `$order=dot_number ASC` query on the
overall query and every page; it was produced by acquisition code that enforced
strict order. The audit accepts that legacy representation only after validating
the exact ordered query and then validates every identifier in the preserved
frame. Malformed arrays and objects, non-object records, invalid UTF-8, records
larger than the fixed 64 MiB corruption guard, trailing/incomplete JSON,
digest/count differences, ordering violations, and provenance inconsistencies
continue to fail closed as `COMPLETE_FRAME_BLOCKED`.

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
