#!/usr/bin/env python3
"""Acquire a small, deterministic FMCSA ingestion cohort (never a frame)."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DATASET_ID = "az4n-8mr2"
DATASET_NAME = "Company Census File"
AGENCY = "U.S. DOT / Federal Motor Carrier Safety Administration"
BASE = f"https://data.transportation.gov/resource/{DATASET_ID}.json"
ORDER = "dot_number ASC"
USER_AGENT = "trucking-software-research/bounded-2.0"
SCOPE = {
    "complete_frame": False,
    "random": False,
    "representative": False,
    "selection_method": "first requested_limit rows returned by deterministic dot_number ASC query",
    "allowed_use": "bounded ingestion and semantic-binding research only",
}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def canonical_json(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def sha256_bytes(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def parse_dot_number(row):
    if not isinstance(row, dict):
        raise ValueError("bounded response must be a JSON array of objects")
    value = row.get("dot_number")
    if value in (None, "") or isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError("bounded response has a missing or invalid dot_number")
    try:
        return int(value)
    except (ValueError, OverflowError) as error:
        raise ValueError("bounded response has a missing or invalid dot_number") from error


def validate_rows(rows, limit):
    if not isinstance(rows, list):
        raise ValueError("FMCSA endpoint did not return a JSON array")
    if len(rows) > limit:
        raise ValueError("FMCSA endpoint returned more rows than requested")
    previous = None
    for row in rows:
        current = parse_dot_number(row)
        if previous is not None and current <= previous:
            reason = "duplicate" if current == previous else "ordering"
            raise ValueError(f"bounded response violates dot_number {reason} contract")
        previous = current


class HttpTransport:
    def get_json(self, url):
        request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        with urlopen(request, timeout=60) as response:
            return json.loads(response.read())


def query_for(limit):
    return {"$limit": limit, "$offset": 0, "$order": ORDER}


def acquire(limit, transport=None, raw_path=None, manifest_path=None, clock=utc_now):
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 5000:
        raise ValueError("limit must be between 1 and 5000")
    query = query_for(limit)
    url = BASE + "?" + urlencode(query)
    rows = (transport or HttpTransport()).get_json(url)
    validate_rows(rows, limit)

    raw_path = Path(raw_path or f"data/raw/fmcsa/company-census-bounded-{limit}.json")
    manifest_path = Path(manifest_path or f"data/derived/fmcsa/bounded-{limit}-manifest.json")
    if raw_path.resolve() == manifest_path.resolve():
        raise ValueError("raw and manifest paths must be distinct")
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    raw_bytes = canonical_json(rows) + b"\n"
    raw_path.write_bytes(raw_bytes)

    manifest = {
        "manifest_format": "fmcsa-bounded-cohort-manifest-v1",
        "status": "BOUNDED_COHORT_ACQUIRED",
        "dataset_identity": {"id": DATASET_ID, "name": DATASET_NAME, "agency": AGENCY},
        "retrieved_at": clock(),
        "query_contract": {"endpoint": BASE, "parameters": query},
        "requested_limit": limit,
        "row_count": len(rows),
        "content_digest": sha256_bytes(raw_bytes),
        "ordering_contract": {
            "field": "dot_number", "direction": "ascending", "strict": True,
            "missing_identifiers": "reject", "duplicate_identifiers": "reject",
        },
        "missing_dot_number_count": 0,
        "duplicate_dot_number_count": 0,
        "scope": SCOPE,
    }
    manifest_path.write_bytes(canonical_json(manifest) + b"\n")
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args(argv)
    try:
        result = acquire(args.limit)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"BOUNDED_COHORT_BLOCKED: {error}")
        return 2
    print(f"{result['status']}: {result['row_count']} rows; {result['content_digest']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
