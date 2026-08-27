#!/usr/bin/env python3
"""Verify that a locally acquired FMCSA frame and schema match their manifest."""
import argparse
import codecs
import hashlib
import json
import re
from pathlib import Path

RAW = Path("data/raw/fmcsa/company-census-complete.json")
MANIFEST = Path("data/derived/fmcsa/complete-frame-manifest.json")
SCHEMA = Path("data/fmcsa/company-census-schema.json")
DATASET_IDENTITY = {
    "id": "az4n-8mr2",
    "name": "Company Census File",
    "agency": "U.S. DOT / Federal Motor Carrier Safety Administration",
}
DATASET_ENDPOINT = "https://data.transportation.gov/resource/az4n-8mr2.json"
SCHEMA_SOURCE = "https://data.transportation.gov/api/views/az4n-8mr2/columns.json"
ORDER = "dot_number ASC"
ORDERING_CONTRACT = {
    "field": "dot_number",
    "direction": "ascending",
    "strict": True,
    "missing_identifiers": "reject",
    "duplicate_identifiers": "reject",
}
READ_CHUNK_SIZE = 1024 * 1024
# A corrupt element with no closing delimiter must not make memory grow to the
# size of the artifact. This is far above the size of an FMCSA census record.
MAX_RECORD_BYTES = 64 * 1024 * 1024
NON_WHITESPACE = re.compile(r"[^ \t\r\n]")


def canonical_digest(value):
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


class DigestingTextReader:
    """Incrementally decode and hash bounded chunks of a UTF-8 JSON artifact."""

    def __init__(self, stream, chunk_size=READ_CHUNK_SIZE):
        self.stream = stream
        self.chunk_size = chunk_size
        self.buffer = ""
        self.offset = 0
        self.digest = hashlib.sha256()
        self.decoder = codecs.getincrementaldecoder("utf-8")()
        self.json_decoder = json.JSONDecoder()
        self.bytes_read = 0
        self.eof = False

    def compact(self):
        if self.offset:
            self.buffer = self.buffer[self.offset:]
            self.offset = 0

    def read_more(self):
        if self.eof:
            return False
        # Normally all prior text has been consumed. Compacting here bounds the
        # buffer to one read chunk plus the one record crossing its boundary.
        self.compact()
        chunk = self.stream.read(self.chunk_size)
        if chunk:
            self.digest.update(chunk)
            self.bytes_read += len(chunk)
            try:
                self.buffer += self.decoder.decode(chunk, final=False)
            except UnicodeDecodeError as error:
                raise ValueError(f"complete frame is not valid UTF-8: {error}") from error
            return True
        try:
            self.buffer += self.decoder.decode(b"", final=True)
        except UnicodeDecodeError as error:
            raise ValueError(f"complete frame is not valid UTF-8: {error}") from error
        self.eof = True
        return False

    def non_whitespace(self):
        while True:
            match = NON_WHITESPACE.search(self.buffer, self.offset)
            if match:
                self.offset = match.end()
                return match.group()
            self.offset = len(self.buffer)
            if not self.read_more():
                return None

    def read_object(self):
        """Decode one object without retaining any other complete-frame bytes."""
        start = self.offset - 1
        record_start_bytes = self.bytes_read
        while True:
            try:
                row, end = self.json_decoder.raw_decode(self.buffer, start)
            except RecursionError as error:
                raise ValueError("complete frame contains excessively nested JSON") from error
            except json.JSONDecodeError as error:
                # The current chunk may end in the middle of a valid object. A
                # record cannot consume more than the fixed corruption guard,
                # plus at most one already-read chunk beyond its exact end.
                if self.bytes_read - record_start_bytes > MAX_RECORD_BYTES + self.chunk_size:
                    raise ValueError(
                        "complete frame contains an unreasonably large, malformed, or unterminated record"
                    ) from error
                self.offset = start
                if self.read_more():
                    start = 0
                    continue
                raise ValueError(f"complete frame contains malformed or incomplete JSON: {error}") from error
            if not isinstance(row, dict):
                raise ValueError("complete frame must be a JSON array of objects")
            # Character count is a cheap lower bound; encode only records near
            # the guard where UTF-8 byte length can affect the decision.
            record = self.buffer[start:end]
            if len(record) > MAX_RECORD_BYTES or (
                    len(record) > MAX_RECORD_BYTES // 4
                    and len(record.encode("utf-8")) > MAX_RECORD_BYTES):
                raise ValueError("complete frame contains an unreasonably large record")
            self.offset = end
            return row


def stream_objects(raw_path, artifact_hash):
    """Yield objects from one top-level JSON array and hash the exact bytes."""
    with raw_path.open("rb") as stream:
        reader = DigestingTextReader(stream)
        if reader.non_whitespace() != "[":
            raise ValueError("complete frame must be a JSON array of objects")
        value = reader.non_whitespace()
        if value == "]":
            if reader.non_whitespace() is not None:
                raise ValueError("complete frame has content after its JSON array")
            artifact_hash.append(reader.digest)
            return
        while True:
            if value != "{":
                raise ValueError("complete frame must be a JSON array of objects")
            yield reader.read_object()
            delimiter = reader.non_whitespace()
            if delimiter == "]":
                if reader.non_whitespace() is not None:
                    raise ValueError("complete frame has content after its JSON array")
                artifact_hash.append(reader.digest)
                return
            if delimiter != ",":
                raise ValueError("complete frame contains malformed JSON array separators")
            value = reader.non_whitespace()
            if value is None or value == "]":
                raise ValueError("complete frame contains an incomplete or trailing array element")


def validate_ordering_contract(manifest):
    query = manifest.get("query_contract")
    if not isinstance(query, dict):
        raise ValueError("manifest query contract is missing or malformed")
    if query.get("endpoint") != DATASET_ENDPOINT or query.get("order") != ORDER:
        raise ValueError("manifest does not declare the canonical dot_number ordering query")
    if query.get("pagination") != "$limit/$offset":
        raise ValueError("manifest pagination contract is not canonical")
    page_size = query.get("page_size")
    if isinstance(page_size, bool) or not isinstance(page_size, int) or page_size < 1:
        raise ValueError("manifest page-size contract is invalid")
    ordering = manifest.get("ordering_contract")
    # Manifests published before the explicit ordering field are legitimate:
    # the exact ordered query was recorded and acquisition enforced this same
    # strict invariant. Every frame is independently checked below. New
    # manifests must carry the explicit field emitted by the acquirer.
    if ordering is not None and ordering != ORDERING_CONTRACT:
        raise ValueError("manifest dot_number ordering contract is not canonical")


def parse_dot_number(value):
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError("dot_number is not an integer identifier")
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("dot_number is not an integer identifier") from error


def audit(raw_path, manifest_path, schema_path):
    manifest = json.loads(manifest_path.read_text())
    schema = json.loads(schema_path.read_text())
    if not isinstance(manifest, dict) or not isinstance(schema, dict):
        raise ValueError("manifest and schema must be JSON objects")
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
    validate_ordering_contract(manifest)

    row_count = missing = duplicates = 0
    previous_dot_number = None
    artifact_hash = []
    for row in stream_objects(raw_path, artifact_hash):
        row_count += 1
        value = row.get("dot_number")
        if value in (None, ""):
            missing += 1
            continue
        dot_number = parse_dot_number(value)
        if previous_dot_number is not None:
            if dot_number < previous_dot_number:
                raise ValueError("complete frame violates ascending dot_number ordering")
            if dot_number == previous_dot_number:
                duplicates += 1
        previous_dot_number = dot_number

    actual_digest = "sha256:" + artifact_hash[0].hexdigest()
    if actual_digest != manifest.get("content_digest"):
        raise ValueError("complete-frame content digest does not match manifest")
    if row_count != manifest.get("row_count"):
        raise ValueError("complete-frame row count does not match manifest")
    if duplicates != manifest.get("duplicate_dot_number_count") or missing != manifest.get("missing_dot_number_count"):
        raise ValueError("identifier audit does not match manifest")
    return {"status": manifest.get("status"), "row_count": row_count, "content_digest": actual_digest,
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
