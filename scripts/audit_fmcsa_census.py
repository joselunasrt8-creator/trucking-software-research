#!/usr/bin/env python3
"""Verify that a locally acquired FMCSA frame and schema match their manifest."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

RAW = Path("data/raw/fmcsa/company-census-complete.json")
MANIFEST = Path("data/derived/fmcsa/complete-frame-manifest.json")
SCHEMA = Path("data/fmcsa/company-census-schema.json")
DATASET_IDENTITY = {
    "id": "az4n-8mr2",
    "name": "Company Census File",
    "agency": "U.S. DOT / Federal Motor Carrier Safety Administration",
}
SCHEMA_SOURCE = "https://data.transportation.gov/api/views/az4n-8mr2/columns.json"


def canonical_digest(value):
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def audit(raw_path, manifest_path, schema_path):
    raw = raw_path.read_bytes()
    manifest = json.loads(manifest_path.read_text())
    schema = json.loads(schema_path.read_text())
    manifest_dataset = manifest.get("dataset_identity", {})
    if any(manifest_dataset.get(key) != value for key, value in DATASET_IDENTITY.items()):
        raise ValueError("manifest dataset identity is not the expected FMCSA Company Census dataset")
    if schema.get("dataset") != DATASET_IDENTITY:
        raise ValueError("schema dataset identity does not match the expected FMCSA Company Census dataset")
    schema_identity = manifest.get("schema_identity", {})
    if schema_identity.get("source_url") != SCHEMA_SOURCE or schema.get("source_url") != SCHEMA_SOURCE:
        raise ValueError("schema source identity does not match the official FMCSA columns endpoint")
    if canonical_digest(schema) != schema_identity.get("digest"):
        raise ValueError("schema artifact digest does not match manifest")
    if schema.get("content_digest") != schema_identity.get("source_content_digest"):
        raise ValueError("schema source-content digest does not match manifest")
    records = json.loads(raw)
    if not isinstance(records, list) or any(not isinstance(row, dict) for row in records):
        raise ValueError("complete frame must be a JSON array of objects")
    actual_digest = "sha256:" + hashlib.sha256(raw).hexdigest()
    if actual_digest != manifest.get("content_digest"):
        raise ValueError("complete-frame content digest does not match manifest")
    if len(records) != manifest.get("row_count"):
        raise ValueError("complete-frame row count does not match manifest")
    dots = [str(row["dot_number"]) for row in records if row.get("dot_number") not in (None, "")]
    duplicates = sum(count - 1 for count in Counter(dots).values() if count > 1)
    missing = len(records) - len(dots)
    if duplicates != manifest.get("duplicate_dot_number_count") or missing != manifest.get("missing_dot_number_count"):
        raise ValueError("identifier audit does not match manifest")
    return {"status": manifest.get("status"), "row_count": len(records), "content_digest": actual_digest,
            "duplicate_dot_number_count": duplicates, "missing_dot_number_count": missing}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, default=RAW)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--schema", type=Path, default=SCHEMA)
    args = parser.parse_args(argv)
    try:
        result = audit(args.raw, args.manifest, args.schema)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"COMPLETE_FRAME_BLOCKED: {error}")
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
