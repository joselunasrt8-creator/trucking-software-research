# FMCSA Company Census empirical boundary (Issue #6)

## Current execution status

The authoritative hosts were unreachable from one complete-frame implementation
environment (the proxy returned HTTP 403). PR #19 nevertheless reports a
successful audit of a preserved 4,490,646-row real frame. Its large ignored
evidence package is unavailable in this checkout, so it cannot be reverified or
used to execute Issue #21 here. No eligible frame is claimed. Current status is:

```text
SEMANTIC_BINDING_PARTIALLY_BOUND
CODEX_ENVIRONMENT_BLOCKED
ISSUE_21_UNRESOLVED
```

The code path is fixture-tested, but fixture values are not empirical results.
The bounded acquisition and its semantic limitation are recorded below and in
`execution-status.json`.

## Bounded ingestion cohort (2026-08-28)

`company-census-bounded-100.json` is a deterministic ingestion cohort selected
by the exact query `$limit=100&$offset=0&$order=dot_number ASC` against dataset
`az4n-8mr2`. Its manifest is `data/derived/fmcsa/bounded-100-manifest.json`.
Run:

```bash
python3 scripts/audit_fmcsa_census_bounded.py --expected-limit 100
```

The audit independently verifies dataset/query identity, requested limit, actual
row count, strict numeric DOT ordering, missing/duplicate identifiers, the
SHA-256 of the exact raw bytes, manifest consistency, and the required scope
disclaimers. The preserved artifact currently yields
`BOUNDED_COHORT_AUDIT_PASSED` with 100 rows, zero missing DOT numbers, zero
duplicates, and digest
`sha256:0d5b09ce940d0d22c7fba5eaee72c3904532a3e1bd77c33066fe0c7c3f59e9e6`.

This is the first 100 results under the declared order. It is not random,
representative, or a complete population frame and cannot support prevalence or
population claims.

## Semantic binding and qualification boundary

The official column response is preserved as
`company-census-columns-official.json`. Its coded-field descriptions are blank.
The DOT dataset metadata retrieved on 2026-08-29, however, identifies FMCSA's
attached **MCMIS Company Census File Data Dictionary, Revision 8 (2026-01-23)**.
Both the metadata response and exact 872,158-byte PDF are preserved under
`data/fmcsa/authoritative/` and SHA-256-bound in
`company-census-semantic-binding.json`.

The dictionary supports these exact transitions:

| Field | Result | Authoritatively bound codes | Remaining dependency |
|---|---|---|---|
| `status_code` | `AUTHORITATIVE_DEFINITION_AVAILABLE` | `A` Active; `I` Inactive; `P` Pending, with the dictionary's full qualifications | none in the documented domain |
| `carrier_operation` | `AUTHORITATIVE_DEFINITION_AVAILABLE` | `A` Interstate; `B` Intrastate HM; `C` Intrastate non-HM | none in the documented domain |
| `safety_rating` | `AUTHORITATIVE_DEFINITION_AVAILABLE` | `S` Satisfactory; `C` Conditional; `U` Unsatisfactory; blank means no Safety/Compliance Review conducted | none in the documented domain |
| `docket1_status_code` | `AUTHORITATIVE_DEFINITION_UNAVAILABLE` | `A` Active; `I` Inactive | current DOT metadata reports `P`, but Revision 8 does not define it |
| `review_type` | `AUTHORITATIVE_DEFINITION_UNAVAILABLE` | `C,H,N,A,S,E,U,K,F,G,I,J` and null/blank as individually defined in Revision 8 | the summary lists `B` without a meaning and disagrees with the detailed list's `K` |

`PROHIBITED_INFERENCE` remains mandatory for all five fields. Run
`python3 scripts/verify_fmcsa_semantic_binding.py` to verify official-host
identity, preserved-byte digests/sizes, attachment identity, citations, code
inventories, semantic transitions, and the not-frozen eligibility state.

Observed letters, frequencies, field names, and labels are not definitions.
No eligible subset is produced. Exact current downstream states are:

```text
SEMANTIC_BINDING_PARTIALLY_BOUND
ELIGIBILITY_RULE_NOT_FROZEN
PROSPECTIVE_QUALIFICATION_NOT_STARTED
```

The next empirical dependency is authoritative FMCSA clarification of
`docket1_status_code=P` and `review_type=B` (including resolution of the
Revision 8 `B`/`K` discrepancy), plus authoritative binding of every separate
field needed to establish for-hire property operation. Only after all selected
inputs are bound may the reference time, inclusion/exclusion predicates,
missing-data behavior, and deterministic logic be preregistered and frozen.

### Path A / Path B decision (2026-08-28)

Path A did not resolve either dictionary defect. No official FMCSA/DOT source
located in the targeted search defines docket status `P`, review type `B`, or
reconciles the Revision 8 summary's `B` with the detailed table's `K`. Those
values remain `AUTHORITATIVE_DEFINITION_UNAVAILABLE`; inference is prohibited.

Path B identified a minimal alternative candidate: Company Census
`status_code=A` (active) and `carrier_operation=A` (interstate), joined by USDOT
number to a MOTUS authority row whose `op_auth_type` is `Motor Carrier of
Property (Except Household Goods)` and whose `op_auth_status` is `Active`.
FMCSA's official operating-authority page defines that authority as an
authorized for-hire motor carrier transporting regulated commodities for the
public for payment, and its official OP-1 instructions state that an ACTIVE
authority registration is required before operation. The preserved MOTUS
metadata and May 18, 2026 dictionary bind the dataset, fields, attachment, and
source bytes. Direct preservation of the two supporting FMCSA pages/documents
are now preserved locally and bound by exact byte size and SHA-256.

Accordingly, `carrier-eligibility-rule-candidate.json` is deterministic but
strictly `CANDIDATE_ONLY`: null, missing, unmatched, and unknown inputs fail
closed as `INDETERMINATE_EXCLUDE`; one joined authority row must satisfy both
authority conditions. `docket1_status_code`, `review_type`, and `safety_rating`
are not dependencies of this target predicate. Run
`python3 scripts/verify_fmcsa_eligibility_candidate.py` to verify the dependency
set, prohibited inputs, deterministic predicates, and unfrozen status. No
carrier results are produced.

### Issue #21 bounded re-evaluation (2026-08-28)

The machine-readable record for this checkout is
`issue-21-codex-environment-status.json`. Verify it without acquiring data,
joining datasets, transforming rows, or sampling with:

```bash
python3 scripts/verify_fmcsa_issue21_environment.py
```

Exit status `2` and `CODEX_ENVIRONMENT_BLOCKED` are the expected successful
environment-boundary result. This is not an authoritative terminal Issue #21
determination.

PR #19 reports a successful audit of the preserved real Company Census frame:
5,103,345,155 bytes, 4,490,646 rows, exact raw SHA-256 and row-count matches to
the acquisition manifest, zero missing or duplicate `dot_number` values, and
validated complete numeric ordering. The merge is preserved as commit
`6ec952b69353bc6bc86a45beb11b667f0a8ffad8`. This historical empirical report
must not be overwritten merely because its large artifacts are not carried by
this checkout.

The current Codex checkout does not contain the ignored raw frame, acquisition
manifest, acquisition-bound schema, or preserved audit output needed to execute
Issue #21. That is an environment access limitation, not evidence that the
historical frame never existed and not an empirical complete-frame failure.

Issue #21 is therefore unresolved in this repository state. Resolution requires
execution in an environment with access to the preserved PR #19 raw frame,
acquisition manifest, bound schema, and successful audit, followed by validation
of those exact objects before transformation. No eligible frame, exclusion
counts, or eligible-frame digest has been produced. Issue #7 remains blocked;
no sample or qualification outcome has been inspected.

The bounded determination for this execution environment is:

```text
CODEX_ENVIRONMENT_BLOCKED
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
`AUTHORIZED_BY_ISSUE_25_ATTEMPT_BLOCKED`. Issue #25 supplied the explicit
authorization and a new identity was assigned before any row acquisition.
`issue-25-acquisition-attempt.json` preserves that identity, the canonical
endpoints and contracts, the attempt timestamp, and the exact result.

The attempt stopped at its earliest legitimacy boundary: the authoritative
Socrata columns endpoint returned HTTP 403 before any response content was
received. No schema artifact could be identity-bound, so the complete-frame row
request was not started and no frame, manifest, page provenance, or audit
artifact was manufactured. Historical unknown identities and recovery findings
remain unchanged. The Issue #25 determination is:

```text
NEW_FMCSA_ACQUISITION_BLOCKED
```

### Preregistered MOTUS / Census temporal alignment

The MOTUS complete frame introduced at commit `5bef755` is now byte-, schema-,
manifest-, dataset-version-, and commit-bound in
`temporal-alignment-contract.json`. Before any joined outcome is inspected, the
contract fixes the reference time as the later `rowsUpdatedAt` marker and caps
the permitted marker skew at 86,400 seconds. The bound MOTUS marker and the
already preserved Census metadata marker differ by 80,794 seconds. This supports
only a contemporaneous administrative-snapshot interpretation, not a claim that
either source records event-effective state at the reference instant.

No admissible Census empirical object is present. The bounded 100-row cohort is
expressly ineligible. The machine-readable determination is
`temporal-alignment-determination.json`; verify it with:

```bash
python3 scripts/verify_fmcsa_temporal_alignment.py
```

Exit status `2` and
`BLOCKED_EXACT_CENSUS_VERSION_UNAVAILABLE` are required in this checkout. A
valid checkpoint preserves 1,400,000 rows at `rowsUpdatedAt=1787919159`, but no
terminal page or remaining suffix. Because the source exposes no immutable
historical snapshot selector, the mutable live endpoint cannot legitimately
complete that prefix. A changed live Census version is not a substitute under
this contract; it requires a newly versioned preregistration and contemporarily
aligned inputs. No join, qualification count, or eligibility freeze has been
produced.

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
| `dot_number` | official metadata identifies a numeric field but supplies no description | stable carrier identity and ordering in the bounded protocol | does not establish eligibility | required for ingestion integrity only |
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
