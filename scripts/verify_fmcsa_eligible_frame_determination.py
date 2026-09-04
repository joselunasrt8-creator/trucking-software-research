#!/usr/bin/env python3
"""Fail-closed verification of the bounded Issue #21 determination."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
DETERMINATION = ROOT / "data/fmcsa/eligible-frame-determination.json"
FINAL = "ELIGIBLE_FRAME_BLOCKED"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def verify(path=DETERMINATION, root=ROOT):
    errors = []
    try:
        value = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as error:
        return {"determination": "ELIGIBLE_FRAME_DETERMINATION_INVALID", "errors": [str(error)]}

    if value.get("determination_format") != "fmcsa-eligible-frame-determination-v1":
        errors.append("unsupported determination format")
    if value.get("determination") != FINAL:
        errors.append("determination must fail closed")
    if value.get("source_dataset", {}).get("id") != "az4n-8mr2":
        errors.append("canonical dataset identity mismatch")

    for field in ("required_complete_frame", "required_acquisition_manifest", "required_schema"):
        record = value.get(field, {})
        artifact = root / record.get("path", "")
        if record.get("present") or artifact.is_file():
            errors.append(f"{field} absence assertion does not match the checkout")
        if any(record.get(key) is not None for key in record if key.endswith("sha256")):
            errors.append(f"{field} assigns an unverified digest")

    audit = value.get("required_real_frame_audit", {})
    if audit.get("present") or audit.get("successful") or (root / audit.get("path", "")).is_file():
        errors.append("successful real-frame audit must not be asserted")

    for binding in value.get("bound_repository_evidence", []):
        artifact = root / binding.get("path", "")
        if not artifact.is_file():
            errors.append(f"bound evidence is missing: {binding.get('path')}")
        elif sha256(artifact) != binding.get("sha256"):
            errors.append(f"bound evidence digest mismatch: {binding.get('path')}")

    expected_implementations = {
        "acquisition_implementation_sha256": root / "scripts/acquire_fmcsa_census.py",
        "audit_implementation_sha256": root / "scripts/audit_fmcsa_census.py",
    }
    identities = value.get("implementation_identities", {})
    for key, artifact in expected_implementations.items():
        if sha256(artifact) != identities.get(key):
            errors.append(f"implementation identity mismatch: {key}")

    issue_6 = value.get("issue_6_determinations", {})
    if issue_6.get("complete_frame") != "COMPLETE_FRAME_BLOCKED" or issue_6.get("schema") != "SCHEMA_NOT_BOUND":
        errors.append("Issue #6 determinations do not fail closed")
    frame = value.get("eligible_frame", {})
    if frame.get("materialized") or frame.get("row_count") is not None or frame.get("sha256") is not None:
        errors.append("an eligible frame is asserted despite blocked prerequisites")
    if frame.get("exclusion_counts_by_reason") is not None or frame.get("reproducibility_runs") != 0:
        errors.append("transformation results are asserted despite blocked prerequisites")
    for boundary in ("issue_7_unblocked", "sample_drawn", "qualification_outcomes_inspected",
                     "broker_or_platform_observation_performed"):
        if value.get(boundary) is not False:
            errors.append(f"hard boundary violated: {boundary}")

    return {"determination": FINAL if not errors else "ELIGIBLE_FRAME_DETERMINATION_INVALID", "errors": errors}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--determination", type=Path, default=DETERMINATION)
    args = parser.parse_args(argv)
    result = verify(args.determination)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 2 if result["determination"] == FINAL else 1


if __name__ == "__main__":
    raise SystemExit(main())
