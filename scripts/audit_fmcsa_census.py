#!/usr/bin/env python3
"""Verify that a locally acquired FMCSA complete frame matches its manifest."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

RAW = Path("data/raw/fmcsa/company-census-complete.json")
MANIFEST = Path("data/derived/fmcsa/complete-frame-manifest.json")


def audit(raw_path, manifest_path):
    raw = raw_path.read_bytes()
    manifest = json.loads(manifest_path.read_text())
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
    args = parser.parse_args(argv)
    try:
        result = audit(args.raw, args.manifest)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"COMPLETE_FRAME_BLOCKED: {error}")
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
