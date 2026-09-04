#!/usr/bin/env python3
"""Verify this checkout's bounded Issue #21 execution-environment status."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
STATUS = ROOT / "data/fmcsa/issue-21-codex-environment-status.json"
ENVIRONMENT_BLOCKED = "CODEX_ENVIRONMENT_BLOCKED"


def verify(path=STATUS, root=ROOT):
    errors = []
    try:
        value = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as error:
        return {"environment_determination": "ENVIRONMENT_STATUS_INVALID", "errors": [str(error)]}

    if value.get("status_format") != "fmcsa-issue-21-codex-environment-status-v1":
        errors.append("unsupported environment-status format")
    if value.get("environment_determination") != ENVIRONMENT_BLOCKED:
        errors.append("current checkout must be represented by its observed environment status")
    if value.get("source_dataset", {}).get("id") != "az4n-8mr2":
        errors.append("canonical dataset identity mismatch")

    historical = value.get("historical_empirical_evidence", {})
    expected_history = {
        "merge_commit": "6ec952b69353bc6bc86a45beb11b667f0a8ffad8",
        "status": "SUCCESSFUL_REAL_FRAME_AUDIT_REPORTED",
        "reported_complete_frame_byte_size": 5103345155,
        "reported_complete_frame_row_count": 4490646,
        "reported_missing_dot_number_count": 0,
        "reported_duplicate_dot_number_count": 0,
        "reported_complete_numeric_ordering_validated": True,
    }
    for key, expected in expected_history.items():
        if historical.get(key) != expected:
            errors.append(f"historical PR #19 evidence mismatch: {key}")
    if historical.get("current_checkout_reverification") != "NOT_POSSIBLE_ARTIFACTS_UNAVAILABLE":
        errors.append("current checkout must not claim reverification of PR #19 artifacts")

    artifacts = value.get("current_environment_evidence", {}).get("required_artifacts", [])
    expected_paths = {
        "data/raw/fmcsa/company-census-complete.json",
        "data/derived/fmcsa/complete-frame-manifest.json",
        "data/fmcsa/company-census-schema.json",
        "data/derived/fmcsa/complete-frame-audit.json",
    }
    if {record.get("path") for record in artifacts} != expected_paths:
        errors.append("required artifact inventory mismatch")
    for record in artifacts:
        artifact = root / record.get("path", "")
        if record.get("present") != artifact.is_file():
            errors.append(f"current-checkout presence mismatch: {record.get('path')}")

    issue = value.get("issue_21", {})
    if issue.get("authoritative_status") != "UNRESOLVED":
        errors.append("checkout evidence must not assert a terminal Issue #21 determination")
    if issue.get("eligible_frame_constructed") is not False:
        errors.append("eligible frame must not be asserted as constructed")
    for key in ("eligible_frame_row_count", "eligible_frame_sha256", "exclusion_counts_by_reason"):
        if issue.get(key) is not None:
            errors.append(f"unexecuted eligible-frame result must remain null: {key}")
    if value.get("issue_7_unblocked") is not False:
        errors.append("Issue #7 must remain blocked")
    for boundary, performed in value.get("hard_boundaries", {}).items():
        if performed is not False:
            errors.append(f"hard boundary violated: {boundary}")

    determination = ENVIRONMENT_BLOCKED if not errors else "ENVIRONMENT_STATUS_INVALID"
    return {"environment_determination": determination, "issue_21": "UNRESOLVED", "errors": errors}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", type=Path, default=STATUS)
    args = parser.parse_args(argv)
    result = verify(args.status)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 2 if result["environment_determination"] == ENVIRONMENT_BLOCKED else 1


if __name__ == "__main__":
    raise SystemExit(main())
