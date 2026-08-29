#!/usr/bin/env python3
"""Fail-closed verifier for MOTUS semantics and the candidate freeze boundary."""
import argparse
import hashlib
import json
from pathlib import Path

SEMANTICS = Path("data/fmcsa/motus-candidate-semantic-evidence.json")
FREEZE = Path("data/fmcsa/candidate-eligibility-freeze.json")
VALUES = {
    "op_auth_type": "Motor Carrier of Property (Except Household Goods)",
    "op_auth_status": "Active",
}


def digest(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def verify(semantics_path=SEMANTICS, freeze_path=FREEZE, root=Path(".")):
    semantics = json.loads(semantics_path.read_text())
    freeze = json.loads(freeze_path.read_text())
    errors = []
    bindings = semantics.get("candidate_bindings", [])
    by_field = {item.get("field"): item for item in bindings if isinstance(item, dict)}
    freeze_grade = True
    for field, value in VALUES.items():
        item = by_field.get(field)
        if not item or item.get("candidate_value") != value:
            errors.append(f"{field}: exact candidate binding is absent or changed")
            freeze_grade = False
            continue
        artifact = item.get("authoritative_artifact")
        text = item.get("authoritative_text")
        if not isinstance(artifact, dict) or not isinstance(text, str) or value not in text:
            freeze_grade = False
            continue
        required = ("path", "url", "identifier", "retrieved_at", "byte_size", "sha256")
        if any(artifact.get(key) in (None, "") for key in required):
            errors.append(f"{field}: authoritative provenance is incomplete")
            freeze_grade = False
            continue
        path = root / artifact["path"]
        if (not path.is_file() or path.stat().st_size != artifact["byte_size"]
                or digest(path) != artifact["sha256"]):
            errors.append(f"{field}: authoritative artifact identity does not verify")
            freeze_grade = False
    has_protocol = all(freeze.get(key) is not None for key in (
        "reference_time_t0", "admissible_company_census_artifact",
        "admissible_motus_artifact", "join_protocol"))
    if has_protocol and not freeze_grade:
        errors.append("point-in-time protocol exists before semantic prerequisite")
    if freeze.get("cohort_artifact") is not None and not has_protocol:
        errors.append("cohort exists without a valid point-in-time protocol")
    if freeze.get("candidate_cohort_row_count") is not None and freeze.get("cohort_artifact") is None:
        errors.append("cohort row count is claimed without a cohort artifact")
    status = "ELIGIBILITY_RULE_FROZEN" if freeze_grade and has_protocol else "ELIGIBILITY_RULE_NOT_FROZEN"
    if freeze.get("eligibility_rule_status") != status:
        errors.append("declared eligibility status contradicts verified prerequisites")
        status = "ELIGIBILITY_RULE_NOT_FROZEN"
    return {"authoritative_motus_semantics_freeze_grade": freeze_grade,
            "point_in_time_protocol_valid": freeze_grade and has_protocol,
            "eligibility_rule_status": status, "errors": errors}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--semantics", type=Path, default=SEMANTICS)
    parser.add_argument("--freeze", type=Path, default=FREEZE)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    result = verify(args.semantics, args.freeze, args.root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["eligibility_rule_status"] == "ELIGIBILITY_RULE_FROZEN" else 2


if __name__ == "__main__":
    raise SystemExit(main())
