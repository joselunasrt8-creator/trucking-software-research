#!/usr/bin/env python3
"""Fail-closed verifier/evaluator for the candidate FMCSA eligibility rule."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

CANDIDATE = Path("data/fmcsa/carrier-eligibility-rule-candidate.json")
EXPECTED_FIELDS = {
    "az4n-8mr2.status_code", "az4n-8mr2.carrier_operation",
    "inys-ebih.op_auth_type", "inys-ebih.op_auth_status",
}
PROHIBITED = {"docket1_status_code", "review_type"}


def verify(path=CANDIDATE):
    errors = []
    try:
        candidate = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as error:
        return {"determination": "CANDIDATE_RULE_BLOCKED", "errors": [str(error)]}
    if candidate.get("artifact_format") != "fmcsa-carrier-eligibility-candidate-v1":
        errors.append("unsupported candidate format")
    if candidate.get("status") != "CANDIDATE_ONLY" or candidate.get("rule_frozen") is not False:
        errors.append("candidate must remain explicitly unfrozen")
    fields = candidate.get("minimal_fields")
    if not isinstance(fields, list) or set(fields) != EXPECTED_FIELDS or len(fields) != 4:
        errors.append("minimal dependency set is not exact")
    predicates = candidate.get("predicates")
    if not isinstance(predicates, list) or len(predicates) != 4:
        errors.append("exactly four predicates are required")
        predicates = []
    if {item.get("field") for item in predicates if isinstance(item, dict)} != EXPECTED_FIELDS:
        errors.append("predicate fields do not match minimal dependencies")
    for item in predicates:
        if not isinstance(item, dict):
            errors.append("predicate is malformed")
            continue
        if item.get("missing_or_other_behavior") != "INDETERMINATE_EXCLUDE":
            errors.append(f"{item.get('name')}: missing/null behavior must fail closed")
        if item.get("deterministically_computable") is not True:
            errors.append(f"{item.get('name')}: predicate is not deterministic")
    prohibited = set(candidate.get("prohibited_dependencies", []))
    if not PROHIBITED <= prohibited or any(field.split(".")[-1] in PROHIBITED for field in fields or []):
        errors.append("unresolved fields are not prohibited")
    if candidate.get("docket1_status_code_required") is not False or candidate.get("review_type_required") is not False:
        errors.append("unresolved fields must not be required")
    if not candidate.get("freeze_blockers"):
        errors.append("candidate must retain explicit freeze blockers")
    return {"determination": "CANDIDATE_RULE_VERIFIED_UNFROZEN" if not errors else "CANDIDATE_RULE_BLOCKED", "errors": errors}


def evaluate(company, authority_rows):
    required_company = company.get("status_code") == "A" and company.get("carrier_operation") == "A"
    if not required_company:
        return "INDETERMINATE_EXCLUDE" if company.get("status_code") is None or company.get("carrier_operation") is None else "EXCLUDE"
    if not authority_rows:
        return "INDETERMINATE_EXCLUDE"
    complete = False
    incomplete = False
    for row in authority_rows:
        authority_type, authority_status = row.get("op_auth_type"), row.get("op_auth_status")
        if authority_type is None or authority_status is None:
            incomplete = True
            continue
        complete = True
        if authority_type == "Motor Carrier of Property (Except Household Goods)" and authority_status == "Active":
            return "INCLUDE"
    return "EXCLUDE" if complete and not incomplete else "INDETERMINATE_EXCLUDE"


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, default=CANDIDATE)
    args = parser.parse_args(argv)
    result = verify(args.candidate)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["determination"] == "CANDIDATE_RULE_VERIFIED_UNFROZEN" else 2


if __name__ == "__main__":
    raise SystemExit(main())
