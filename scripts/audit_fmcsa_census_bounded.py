#!/usr/bin/env python3
"""Independently audit a bounded FMCSA cohort and its fail-closed scope."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode

from acquire_fmcsa_census_bounded import AGENCY, BASE, DATASET_ID, DATASET_NAME, ORDER, SCOPE, parse_dot_number

DATASET_IDENTITY = {"id": DATASET_ID, "name": DATASET_NAME, "agency": AGENCY}
ORDERING_CONTRACT = {
    "field": "dot_number", "direction": "ascending", "strict": True,
    "missing_identifiers": "reject", "duplicate_identifiers": "reject",
}


def _integer(value, name, minimum=0):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"manifest {name} is invalid")
    return value


def audit(raw_path, manifest_path, expected_limit=None):
    try:
        manifest = json.loads(Path(manifest_path).read_text())
        raw_bytes = Path(raw_path).read_bytes()
        rows = json.loads(raw_bytes)
    except json.JSONDecodeError as error:
        raise ValueError(f"bounded artifact or manifest is malformed JSON: {error}") from error
    if not isinstance(manifest, dict) or manifest.get("manifest_format") != "fmcsa-bounded-cohort-manifest-v1":
        raise ValueError("bounded manifest is malformed or has an incompatible format")
    if manifest.get("status") != "BOUNDED_COHORT_ACQUIRED":
        raise ValueError("bounded manifest status is not canonical")
    if manifest.get("dataset_identity") != DATASET_IDENTITY:
        raise ValueError("bounded manifest dataset identity is not canonical")
    limit = _integer(manifest.get("requested_limit"), "requested_limit", 1)
    if limit > 5000 or (expected_limit is not None and limit != expected_limit):
        raise ValueError("bounded manifest requested limit does not match the audit contract")
    query = {"$limit": limit, "$offset": 0, "$order": ORDER}
    if manifest.get("query_contract") != {"endpoint": BASE, "parameters": query}:
        raise ValueError("bounded manifest query identity is not canonical")
    if manifest.get("ordering_contract") != ORDERING_CONTRACT:
        raise ValueError("bounded manifest ordering contract is not canonical")
    if manifest.get("scope") != SCOPE:
        raise ValueError("bounded manifest must explicitly disclaim complete, random, and representative scope")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("bounded artifact must be a JSON array of objects")
    if len(rows) > limit:
        raise ValueError("bounded artifact exceeds requested limit")

    missing = duplicates = 0
    previous = None
    for row in rows:
        try:
            current = parse_dot_number(row)
        except ValueError:
            missing += 1
            continue
        if previous is not None:
            if current < previous:
                raise ValueError("bounded artifact violates ascending dot_number ordering")
            if current == previous:
                duplicates += 1
        previous = current
    actual_digest = "sha256:" + hashlib.sha256(raw_bytes).hexdigest()
    if actual_digest != manifest.get("content_digest"):
        raise ValueError("bounded artifact digest does not match manifest")
    if len(rows) != _integer(manifest.get("row_count"), "row_count"):
        raise ValueError("bounded artifact row count does not match manifest")
    if missing != manifest.get("missing_dot_number_count") or duplicates != manifest.get("duplicate_dot_number_count"):
        raise ValueError("bounded identifier counts do not match manifest")
    if missing or duplicates:
        raise ValueError("bounded artifact contains missing or duplicate DOT numbers")
    return {
        "status": "BOUNDED_COHORT_AUDIT_PASSED", "requested_limit": limit,
        "row_count": len(rows), "content_digest": actual_digest,
        "missing_dot_number_count": missing, "duplicate_dot_number_count": duplicates,
        "scope": SCOPE, "source_url": BASE + "?" + urlencode(query),
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, default=Path("data/raw/fmcsa/company-census-bounded-100.json"))
    parser.add_argument("--manifest", type=Path, default=Path("data/derived/fmcsa/bounded-100-manifest.json"))
    parser.add_argument("--expected-limit", type=int)
    args = parser.parse_args(argv)
    try:
        result = audit(args.raw, args.manifest, args.expected_limit)
    except (OSError, ValueError) as error:
        print(f"BOUNDED_COHORT_BLOCKED: {error}")
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
