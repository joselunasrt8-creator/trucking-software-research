#!/usr/bin/env python3
"""Acquire a version-bound, deterministically ordered FMCSA Company Census frame."""
from __future__ import annotations

import argparse
import errno
import hashlib
import http.client
import json
import os
import ssl
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
USER_AGENT = "trucking-software-research/3.0"
CHECKPOINT_FORMAT = 1
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
            # A truncated response raises IncompleteRead here, before JSON parsing.
            # retry_get therefore never exposes a partial JSON page to acquisition.
            return json.loads(response.read())


TRANSIENT_ERRNOS = {
    errno.ECONNABORTED,
    errno.ECONNRESET,
    errno.EPIPE,
    errno.ETIMEDOUT,
}
if hasattr(errno, "ENETRESET"):
    TRANSIENT_ERRNOS.add(errno.ENETRESET)


def is_retryable(error):
    if isinstance(error, HTTPError):
        return error.code == 429 or error.code >= 500
    if isinstance(error, http.client.IncompleteRead):
        return True
    if isinstance(error, URLError):
        if isinstance(error.reason, ssl.SSLCertVerificationError):
            return False
        return True
    if isinstance(error, ssl.SSLCertVerificationError):
        return False
    if isinstance(error, ssl.SSLError):
        return True
    if isinstance(error, (TimeoutError, ConnectionError)):
        return True
    return isinstance(error, OSError) and error.errno in TRANSIENT_ERRNOS


def retry_get(transport, url, retries=3, sleep=time.sleep):
    """Retry transient read/transport/server failures; never accept partial JSON."""
    handled = (HTTPError, URLError, http.client.IncompleteRead, ssl.SSLError,
               TimeoutError, ConnectionError, OSError)
    for attempt in range(retries + 1):
        try:
            return transport.get_json(url)
        except handled as error:
            if not is_retryable(error) or attempt == retries:
                raise CompleteFrameBlocked(
                    f"request failed after {attempt + 1} attempt(s): {url}: {error}"
                ) from error
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


def query_contract(page_size):
    return {
        "endpoint": BASE,
        "order": ORDER,
        "pagination": "$limit/$offset",
        "page_size": page_size,
        "termination": "first page with row_count < page_size; includes a possibly empty terminal page",
    }


def checkpoint_path_for(out):
    return out.with_name(out.name + ".checkpoint.json")


def partial_path_for(out):
    return out.with_name(out.name + ".partial")


def temporary_path(destination):
    """Reserve a temporary artifact beside its destination for atomic replacement."""
    descriptor, name = tempfile.mkstemp(prefix=destination.name + ".", suffix=".tmp", dir=destination.parent)
    os.close(descriptor)
    return Path(name)


def fsync_directory(path):
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_write_json(path, value):
    temporary = temporary_path(path)
    try:
        with temporary.open("wb") as stream:
            stream.write(canonical_json(value) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
        fsync_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


def output_identity(out, manifest_path, schema_path, checkpoint_path, partial_path):
    return {
        "raw": str(out.resolve()),
        "manifest": str(manifest_path.resolve()),
        "schema": str(schema_path.resolve()),
        "checkpoint": str(checkpoint_path.resolve()),
        "partial": str(partial_path.resolve()),
    }


def acquisition_contract(out, manifest_path, schema_path, checkpoint_path, partial_path,
                         page_size, rows_updated_at, binding):
    return {
        "checkpoint_format": CHECKPOINT_FORMAT,
        "dataset_identity": {
            "id": DATASET_ID,
            "name": DATASET_NAME,
            "agency": AGENCY,
            "rows_updated_at": rows_updated_at,
        },
        "query_contract": query_contract(page_size),
        "ordering_contract": {
            "field": "dot_number",
            "direction": "ascending",
            "strict": True,
            "missing_identifiers": "reject",
            "duplicate_identifiers": "reject",
        },
        "schema_identity": {
            "source_url": SCHEMA_URL,
            "source_content_digest": binding["content_digest"],
            "binding_digest": digest(binding),
        },
        "serialization_contract": {
            "format": "JSON array followed by LF",
            "row_serialization": "UTF-8 canonical JSON with sorted keys and compact separators",
            "artifact_digest": "SHA-256 over exact published bytes",
        },
        "output_identity": output_identity(
            out, manifest_path, schema_path, checkpoint_path, partial_path
        ),
    }


def initial_state():
    prefix = b"["
    return {
        "next_offset": 0,
        "row_count": 0,
        "previous_dot_number": None,
        "artifact_byte_count": len(prefix),
        "artifact_prefix_digest": "sha256:" + hashlib.sha256(prefix).hexdigest(),
        "terminal_page_received": False,
        "pages": [],
    }


def checkpoint_document(contract, binding, started, state):
    checkpoint = {
        "format": "fmcsa-complete-frame-checkpoint-v1",
        "contract": contract,
        "schema_binding": binding,
        "acquisition_started_at": started,
        "state": state,
    }
    checkpoint["checkpoint_digest"] = digest(checkpoint)
    return checkpoint


def load_checkpoint(path):
    try:
        checkpoint = json.loads(path.read_bytes())
    except (OSError, json.JSONDecodeError) as error:
        raise CompleteFrameBlocked(f"checkpoint is unreadable or malformed: {path}: {error}") from error
    if not isinstance(checkpoint, dict) or checkpoint.get("format") != "fmcsa-complete-frame-checkpoint-v1":
        raise CompleteFrameBlocked("checkpoint has an incompatible format")
    unsealed = dict(checkpoint)
    claimed_digest = unsealed.pop("checkpoint_digest", None)
    if claimed_digest != digest(unsealed):
        raise CompleteFrameBlocked("checkpoint content does not match its integrity digest")
    return checkpoint


def validate_checkpoint_state(state, page_size):
    if not isinstance(state, dict) or not isinstance(state.get("pages"), list):
        raise CompleteFrameBlocked("checkpoint state is malformed")
    pages = state["pages"]
    total = 0
    terminal = False
    for index, page in enumerate(pages):
        expected_offset = index * page_size
        if not isinstance(page, dict) or page.get("page") != index + 1:
            raise CompleteFrameBlocked("checkpoint page provenance is not contiguous")
        if page.get("offset") != expected_offset or page.get("requested_limit") != page_size:
            raise CompleteFrameBlocked("checkpoint page offsets or limits are incompatible")
        if page.get("source_url") != page_url(page_size, expected_offset):
            raise CompleteFrameBlocked("checkpoint page query provenance is incompatible")
        page_digest = page.get("content_digest")
        if (not isinstance(page_digest, str) or len(page_digest) != 71
                or not page_digest.startswith("sha256:")):
            raise CompleteFrameBlocked("checkpoint page content digest is invalid")
        try:
            int(page_digest[7:], 16)
        except ValueError as error:
            raise CompleteFrameBlocked("checkpoint page content digest is invalid") from error
        if not isinstance(page.get("retrieved_at"), str):
            raise CompleteFrameBlocked("checkpoint page retrieval provenance is invalid")
        count = page.get("row_count")
        if isinstance(count, bool) or not isinstance(count, int) or count < 0 or count > page_size:
            raise CompleteFrameBlocked("checkpoint page row count is invalid")
        if terminal or (count < page_size and index != len(pages) - 1):
            raise CompleteFrameBlocked("checkpoint contains pages after a terminal page")
        terminal = count < page_size
        total += count
    expected_next = len(pages) * page_size
    if state.get("next_offset") != expected_next or state.get("row_count") != total:
        raise CompleteFrameBlocked("checkpoint cumulative offset or row count is inconsistent")
    if state.get("terminal_page_received") is not terminal:
        raise CompleteFrameBlocked("checkpoint terminal-page state is inconsistent")
    previous = state.get("previous_dot_number")
    if (total == 0 and previous is not None) or (
            total > 0 and (isinstance(previous, bool) or not isinstance(previous, int))):
        raise CompleteFrameBlocked("checkpoint ordering state is inconsistent")
    byte_count = state.get("artifact_byte_count")
    prefix_digest = state.get("artifact_prefix_digest")
    if isinstance(byte_count, bool) or not isinstance(byte_count, int) or byte_count < 1:
        raise CompleteFrameBlocked("checkpoint artifact byte count is invalid")
    if (not isinstance(prefix_digest, str) or len(prefix_digest) != 71
            or not prefix_digest.startswith("sha256:")):
        raise CompleteFrameBlocked("checkpoint artifact prefix digest is invalid")
    try:
        int(prefix_digest[7:], 16)
    except ValueError as error:
        raise CompleteFrameBlocked("checkpoint artifact prefix digest is invalid") from error


def reconstruct_prefix(partial_path, state):
    committed = state["artifact_byte_count"]
    artifact_hash = hashlib.sha256()
    try:
        stream = partial_path.open("r+b")
    except OSError as error:
        raise CompleteFrameBlocked(f"checkpoint partial artifact is unavailable: {partial_path}: {error}") from error
    try:
        remaining = committed
        while remaining:
            chunk = stream.read(min(1024 * 1024, remaining))
            if not chunk:
                raise CompleteFrameBlocked("partial artifact is shorter than its committed checkpoint prefix")
            artifact_hash.update(chunk)
            remaining -= len(chunk)
        actual = "sha256:" + artifact_hash.hexdigest()
        if actual != state["artifact_prefix_digest"]:
            raise CompleteFrameBlocked("partial artifact does not match its committed checkpoint digest")
        stream.seek(0, os.SEEK_END)
        if stream.tell() > committed:
            stream.truncate(committed)
            stream.flush()
            os.fsync(stream.fileno())
        stream.seek(committed)
        return stream, artifact_hash
    except Exception:
        stream.close()
        raise


def validate_dot_number(row):
    value = row.get("dot_number")
    if value in (None, ""):
        raise CompleteFrameBlocked("missing dot_number prevents a complete keyed carrier frame")
    try:
        if isinstance(value, bool) or not isinstance(value, (str, int)):
            raise ValueError
        return int(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise CompleteFrameBlocked("dot_number is missing or is not an integer identifier") from error


def acquire(transport, out, manifest_path, schema_path, page_size=50000, retries=3,
            clock=utc_now, sleep=time.sleep, checkpoint_path=None):
    if page_size < 1:
        raise ValueError("page_size must be positive")
    if retries < 0:
        raise ValueError("retries must not be negative")
    out, manifest_path, schema_path = Path(out), Path(manifest_path), Path(schema_path)
    checkpoint_path = Path(checkpoint_path) if checkpoint_path is not None else checkpoint_path_for(out)
    partial_path = partial_path_for(out)
    identities = [path.resolve() for path in (
        out, manifest_path, schema_path, checkpoint_path, partial_path
    )]
    if len(set(identities)) != len(identities):
        raise ValueError("raw, manifest, schema, checkpoint, and partial paths must be distinct")
    for path in (out, manifest_path, schema_path, checkpoint_path, partial_path):
        path.parent.mkdir(parents=True, exist_ok=True)

    observed_started = clock()
    before = retry_get(transport, VIEW, retries, sleep)
    columns = retry_get(transport, SCHEMA_URL, retries, sleep)
    observed_binding = schema_binding(columns, clock())
    if not isinstance(before, dict):
        raise CompleteFrameBlocked("dataset metadata endpoint did not return an object")
    version_before = before.get("rowsUpdatedAt")
    if version_before is None:
        raise CompleteFrameBlocked("dataset metadata has no rowsUpdatedAt version marker")

    if checkpoint_path.exists():
        checkpoint = load_checkpoint(checkpoint_path)
        binding = checkpoint.get("schema_binding")
        contract = checkpoint.get("contract")
        if not isinstance(binding, dict) or not isinstance(contract, dict):
            raise CompleteFrameBlocked("checkpoint contract or schema binding is malformed")
        checkpoint_dataset = contract.get("dataset_identity")
        checkpoint_schema = contract.get("schema_identity")
        if not isinstance(checkpoint_dataset, dict) or not isinstance(checkpoint_schema, dict):
            raise CompleteFrameBlocked("checkpoint dataset or schema contract is malformed")
        checkpoint_version = checkpoint_dataset.get("rows_updated_at")
        if checkpoint_version != version_before:
            raise CompleteFrameBlocked(
                "stale checkpoint: dataset rowsUpdatedAt changed across acquisition resume"
            )
        if binding.get("content_digest") != observed_binding["content_digest"]:
            raise CompleteFrameBlocked("stale checkpoint: official schema content changed across resume")
        try:
            expected_contract = acquisition_contract(
                out, manifest_path, schema_path, checkpoint_path, partial_path,
                page_size, version_before, binding,
            )
        except (KeyError, TypeError) as error:
            raise CompleteFrameBlocked("checkpoint schema binding is malformed") from error
        if contract != expected_contract:
            raise CompleteFrameBlocked(
                "incompatible checkpoint: acquisition/query/order/page-size/schema/output contract changed"
            )
        if digest(binding) != checkpoint_schema.get("binding_digest"):
            raise CompleteFrameBlocked("checkpoint schema binding does not match its bound digest")
        state = checkpoint.get("state")
        validate_checkpoint_state(state, page_size)
        started = checkpoint.get("acquisition_started_at")
        if not isinstance(started, str):
            raise CompleteFrameBlocked("checkpoint acquisition start time is malformed")
        raw, artifact_hash = reconstruct_prefix(partial_path, state)
    else:
        if partial_path.exists():
            raise CompleteFrameBlocked("orphaned partial artifact exists without a checkpoint")
        binding = observed_binding
        started = observed_started
        contract = acquisition_contract(
            out, manifest_path, schema_path, checkpoint_path, partial_path,
            page_size, version_before, binding,
        )
        state = initial_state()
        try:
            raw = partial_path.open("xb")
            raw.write(b"[")
            raw.flush()
            os.fsync(raw.fileno())
            fsync_directory(partial_path.parent)
            atomic_write_json(checkpoint_path, checkpoint_document(contract, binding, started, state))
            artifact_hash = hashlib.sha256(b"[")
        except Exception:
            if "raw" in locals():
                raw.close()
            if not checkpoint_path.exists():
                partial_path.unlink(missing_ok=True)
            raise

    staged = []
    try:
        while not state["terminal_page_received"]:
            offset = state["next_offset"]
            url = page_url(page_size, offset)
            page = retry_get(transport, url, retries, sleep)
            if not isinstance(page, list) or any(not isinstance(row, dict) for row in page):
                raise CompleteFrameBlocked(f"page at offset {offset} is not an array of objects")
            if len(page) > page_size:
                raise CompleteFrameBlocked(
                    f"page at offset {offset} exceeds its requested limit"
                )

            candidate_previous = state["previous_dot_number"]
            for row in page:
                dot_number = validate_dot_number(row)
                if candidate_previous is not None:
                    if dot_number == candidate_previous:
                        raise CompleteFrameBlocked(
                            "duplicate dot_number prevents unambiguous carrier deduplication"
                        )
                    if dot_number < candidate_previous:
                        raise CompleteFrameBlocked(
                            "server response violates the declared stable ordering contract"
                        )
                candidate_previous = dot_number

            candidate_count = state["row_count"]
            for row in page:
                chunk = ((b"," if candidate_count else b"") + canonical_json(row))
                raw.write(chunk)
                artifact_hash.update(chunk)
                candidate_count += 1
            raw.flush()
            os.fsync(raw.fileno())

            provenance = {
                "page": len(state["pages"]) + 1,
                "offset": offset,
                "requested_limit": page_size,
                "row_count": len(page),
                "source_url": url,
                "content_digest": digest(page),
                "retrieved_at": clock(),
            }
            state = {
                "next_offset": offset + page_size,
                "row_count": candidate_count,
                "previous_dot_number": candidate_previous,
                "artifact_byte_count": raw.tell(),
                "artifact_prefix_digest": "sha256:" + artifact_hash.hexdigest(),
                "terminal_page_received": len(page) < page_size,
                "pages": state["pages"] + [provenance],
            }
            atomic_write_json(
                checkpoint_path, checkpoint_document(contract, binding, started, state)
            )
            page = None

        raw.write(b"]\n")
        artifact_hash.update(b"]\n")
        raw.flush()
        os.fsync(raw.fileno())
        raw.close()

        after = retry_get(transport, VIEW, retries, sleep)
        if not isinstance(after, dict):
            raise CompleteFrameBlocked("dataset metadata endpoint did not return an object")
        if after.get("rowsUpdatedAt") != version_before:
            raise CompleteFrameBlocked("dataset rowsUpdatedAt changed during pagination")

        completed = clock()
        manifest = {
            "status": "COMPLETE_FRAME_READY_WITH_LIMITATIONS",
            "dataset_identity": {
                "id": DATASET_ID,
                "name": DATASET_NAME,
                "agency": AGENCY,
                "rows_updated_at": version_before,
            },
            "schema_identity": {
                "source_url": SCHEMA_URL,
                "digest": digest(binding),
                "source_content_digest": binding["content_digest"],
                "retrieved_at": binding["retrieved_at"],
            },
            "acquisition_started_at": started,
            "acquisition_completed_at": completed,
            "query_contract": query_contract(page_size),
            "retry_contract": {
                "retries": retries,
                "backoff_seconds": [2**n for n in range(retries)],
                "retryable": [
                    "http.client.IncompleteRead",
                    "socket timeout/read/reset/abort/broken-pipe",
                    "transient SSL read failures (excluding certificate verification)",
                    "URL transport errors",
                    "HTTP 429",
                    "HTTP 5xx",
                ],
            },
            "checkpoint_contract": {
                "format": "fmcsa-complete-frame-checkpoint-v1",
                "commit_unit": "fully received, parsed, validated, canonically serialized, fsynced page",
                "resume_validation": "exact contract plus dataset/schema identity and committed-prefix length/digest",
            },
            "page_count": len(state["pages"]),
            "row_count": state["row_count"],
            "content_digest": "sha256:" + artifact_hash.hexdigest(),
            "duplicate_dot_number_count": 0,
            "missing_dot_number_count": 0,
            "pages": state["pages"],
            "known_limitations": [
                "rowsUpdatedAt is checked before and after pagination; the API does not expose an immutable snapshot selector.",
                "Completeness depends on Socrata rowsUpdatedAt changing for every intervening dataset mutation.",
            ],
        }
        schema_temporary = temporary_path(schema_path)
        manifest_temporary = temporary_path(manifest_path)
        staged.extend((schema_temporary, manifest_temporary))
        with schema_temporary.open("wb") as stream:
            stream.write(canonical_json(binding) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        with manifest_temporary.open("wb") as stream:
            stream.write(canonical_json(manifest) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())

        # Publish only after every artifact is complete. The manifest is the final
        # commit marker, so audit never observes a new manifest before its inputs.
        schema_temporary.replace(schema_path)
        partial_path.replace(out)
        manifest_temporary.replace(manifest_path)
        fsync_directory(out.parent)
        if schema_path.parent != out.parent:
            fsync_directory(schema_path.parent)
        if manifest_path.parent not in (out.parent, schema_path.parent):
            fsync_directory(manifest_path.parent)
        checkpoint_path.unlink()
        fsync_directory(checkpoint_path.parent)
        return manifest
    finally:
        if not raw.closed:
            raw.close()
        for path in staged:
            path.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--page-size", type=int, default=50000)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--checkpoint", type=Path)
    args = parser.parse_args(argv)
    try:
        result = acquire(
            HttpTransport(), args.out, args.manifest, args.schema, args.page_size,
            checkpoint_path=args.checkpoint,
        )
    except CompleteFrameBlocked as error:
        print(f"COMPLETE_FRAME_BLOCKED: {error}")
        return 2
    print(f"{result['status']}: {result['row_count']} rows; {result['content_digest']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
