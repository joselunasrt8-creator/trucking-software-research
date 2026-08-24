#!/usr/bin/env python3
"""Acquire a version-bound, deterministically ordered FMCSA Company Census frame."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DATASET_ID = "az4n-8mr2"
DATASET_NAME = "Company Census File"
AGENCY = "U.S. DOT / Federal Motor Carrier Safety Administration"
BASE = f"https://data.transportation.gov/resource/{DATASET_ID}.json"
VIEW = f"https://data.transportation.gov/api/views/{DATASET_ID}"
SCHEMA_URL = f"{VIEW}/columns.json"
ORDER = "dot_number ASC"
USER_AGENT = "trucking-software-research/2.0"
DEFAULT_OUT = Path("data/raw/fmcsa/company-census-complete.json")
DEFAULT_MANIFEST = Path("data/derived/fmcsa/complete-frame-manifest.json")
DEFAULT_SCHEMA = Path("data/fmcsa/company-census-schema.json")


class CompleteFrameBlocked(RuntimeError):
    """Stable complete-frame acquisition could not be established."""


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def canonical_json(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def digest(value):
    return "sha256:" + hashlib.sha256(canonical_json(value)).hexdigest()


class HttpTransport:
    def get_json(self, url):
        request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        with urlopen(request, timeout=60) as response:
            return json.loads(response.read())


def retry_get(transport, url, retries=3, sleep=time.sleep):
    """Retry transient transport/server failures; never retry malformed success data."""
    for attempt in range(retries + 1):
        try:
            return transport.get_json(url)
        except (HTTPError, URLError, TimeoutError, ConnectionError) as error:
            retryable = not isinstance(error, HTTPError) or error.code == 429 or error.code >= 500
            if not retryable or attempt == retries:
                raise CompleteFrameBlocked(f"request failed after {attempt + 1} attempt(s): {url}: {error}")
            sleep(2**attempt)


def schema_binding(columns, retrieved_at):
    if not isinstance(columns, list) or not columns or any(not isinstance(c, dict) for c in columns):
        raise CompleteFrameBlocked("official columns endpoint did not return a non-empty column array")
    fields = []
    for column in columns:
        field = column.get("fieldName")
        if not field:
            raise CompleteFrameBlocked("official schema contains a column without fieldName")
        fields.append({
            "field": field,
            "authoritative_label": column.get("name"),
            "authoritative_description": column.get("description"),
            "authoritative_type": column.get("dataTypeName"),
            "unresolved_definition": None if column.get("description") else "Official column metadata supplies no description; no semantics inferred.",
        })
    return {
        "dataset": {"id": DATASET_ID, "name": DATASET_NAME, "agency": AGENCY},
        "source_url": SCHEMA_URL,
        "retrieved_at": retrieved_at,
        "content_digest": digest(columns),
        "fields": fields,
    }


def page_url(limit, offset):
    return BASE + "?" + urlencode({"$limit": limit, "$offset": offset, "$order": ORDER})


def temporary_path(destination):
    """Reserve a temporary artifact beside its destination for atomic replacement."""
    descriptor, name = tempfile.mkstemp(prefix=destination.name + ".", suffix=".tmp", dir=destination.parent)
    os.close(descriptor)
    return Path(name)


def acquire(transport, out, manifest_path, schema_path, page_size=50000, retries=3, clock=utc_now, sleep=time.sleep):
    if page_size < 1:
        raise ValueError("page_size must be positive")
    started = clock()
    before = retry_get(transport, VIEW, retries, sleep)
    columns = retry_get(transport, SCHEMA_URL, retries, sleep)
    binding = schema_binding(columns, clock())
    version_before = before.get("rowsUpdatedAt")
    if version_before is None:
        raise CompleteFrameBlocked("dataset metadata has no rowsUpdatedAt version marker")
    for path in (out, manifest_path, schema_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    raw_temporary = temporary_path(out)
    staged = [raw_temporary]
    pages, offset, row_count = [], 0, 0
    missing = duplicates = 0
    previous_dot_number = None
    artifact_hash = hashlib.sha256()
    try:
        with raw_temporary.open("wb") as raw:
            def write(chunk):
                raw.write(chunk)
                artifact_hash.update(chunk)

            write(b"[")
            while True:
                url = page_url(page_size, offset)
                page = retry_get(transport, url, retries, sleep)
                if not isinstance(page, list) or any(not isinstance(row, dict) for row in page):
                    raise CompleteFrameBlocked(f"page at offset {offset} is not an array of objects")
                pages.append({"page": len(pages) + 1, "offset": offset, "requested_limit": page_size,
                              "row_count": len(page), "source_url": url, "content_digest": digest(page),
                              "retrieved_at": clock()})
                for row in page:
                    value = row.get("dot_number")
                    if value in (None, ""):
                        missing += 1
                        raise CompleteFrameBlocked("missing dot_number prevents a complete keyed carrier frame")
                    try:
                        if isinstance(value, bool):
                            raise ValueError
                        if not isinstance(value, (str, int)):
                            raise ValueError
                        dot_number = int(value)
                    except (TypeError, ValueError, OverflowError):
                        raise CompleteFrameBlocked("dot_number is missing or is not an integer identifier")
                    if previous_dot_number is not None:
                        if dot_number == previous_dot_number:
                            duplicates += 1
                            raise CompleteFrameBlocked("duplicate dot_number prevents unambiguous carrier deduplication")
                        if dot_number < previous_dot_number:
                            raise CompleteFrameBlocked("server response violates the declared stable ordering contract")
                    if row_count:
                        write(b",")
                    write(canonical_json(row))
                    row_count += 1
                    previous_dot_number = dot_number
                if len(page) < page_size:
                    break
                offset += page_size
            write(b"]\n")
            raw.flush()
            os.fsync(raw.fileno())

        after = retry_get(transport, VIEW, retries, sleep)
        if after.get("rowsUpdatedAt") != version_before:
            raise CompleteFrameBlocked("dataset rowsUpdatedAt changed during pagination")

        completed = clock()
        manifest = {
            "status": "COMPLETE_FRAME_READY_WITH_LIMITATIONS",
            "dataset_identity": {"id": DATASET_ID, "name": DATASET_NAME, "agency": AGENCY,
                                 "rows_updated_at": version_before},
            "schema_identity": {"source_url": SCHEMA_URL, "digest": digest(binding),
                                "source_content_digest": binding["content_digest"],
                                "retrieved_at": binding["retrieved_at"]},
            "acquisition_started_at": started, "acquisition_completed_at": completed,
            "query_contract": {"endpoint": BASE, "order": ORDER, "pagination": "$limit/$offset",
                               "page_size": page_size,
                               "termination": "first page with row_count < page_size; includes a possibly empty terminal page"},
            "retry_contract": {"retries": retries, "backoff_seconds": [2**n for n in range(retries)],
                               "retryable": ["transport", "timeout", "HTTP 429", "HTTP 5xx"]},
            "page_count": len(pages), "row_count": row_count,
            "content_digest": "sha256:" + artifact_hash.hexdigest(),
            "duplicate_dot_number_count": duplicates, "missing_dot_number_count": missing, "pages": pages,
            "known_limitations": [
                "rowsUpdatedAt is checked before and after pagination; the API does not expose an immutable snapshot selector.",
                "Completeness depends on Socrata rowsUpdatedAt changing for every intervening dataset mutation.",
            ],
        }
        schema_temporary = temporary_path(schema_path)
        manifest_temporary = temporary_path(manifest_path)
        staged.extend((schema_temporary, manifest_temporary))
        schema_temporary.write_bytes(canonical_json(binding) + b"\n")
        manifest_temporary.write_bytes(canonical_json(manifest) + b"\n")

        # Publish only after every artifact is complete. The manifest is the final
        # commit marker, so audit never observes a new manifest before its inputs.
        schema_temporary.replace(schema_path)
        raw_temporary.replace(out)
        manifest_temporary.replace(manifest_path)
        return manifest
    finally:
        for path in staged:
            path.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--page-size", type=int, default=50000)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args(argv)
    try:
        result = acquire(HttpTransport(), args.out, args.manifest, args.schema, args.page_size)
    except CompleteFrameBlocked as error:
        print(f"COMPLETE_FRAME_BLOCKED: {error}")
        return 2
    print(f"{result['status']}: {result['row_count']} rows; {result['content_digest']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
