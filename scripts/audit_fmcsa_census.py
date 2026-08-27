#!/usr/bin/env python3
"""Verify that a locally acquired FMCSA frame and schema match their manifest."""
import argparse
import hashlib
import json
import sqlite3
import tempfile
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
READ_CHUNK_SIZE = 1024 * 1024
# A corrupt element with no closing delimiter must not make memory grow to the
# size of the artifact. This is far above the size of an FMCSA census record.
MAX_RECORD_BYTES = 64 * 1024 * 1024


def canonical_digest(value):
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


class DigestingReader:
    """Small buffered byte reader which hashes every byte exactly once."""

    def __init__(self, stream, chunk_size=READ_CHUNK_SIZE):
        self.stream = stream
        self.chunk_size = chunk_size
        self.chunk = b""
        self.offset = 0
        self.digest = hashlib.sha256()

    def read_byte(self):
        if self.offset == len(self.chunk):
            self.chunk = self.stream.read(self.chunk_size)
            self.offset = 0
            if not self.chunk:
                return None
            self.digest.update(self.chunk)
        value = self.chunk[self.offset]
        self.offset += 1
        return value

    def non_whitespace(self):
        value = self.read_byte()
        while value is not None and value in b" \t\r\n":
            value = self.read_byte()
        return value


def read_object(reader, first):
    """Frame one JSON object without retaining any other complete-frame bytes."""
    record = bytearray([first])
    stack = [ord("}")]
    in_string = False
    escaped = False
    while stack:
        value = reader.read_byte()
        if value is None:
            raise ValueError("complete frame contains an incomplete JSON object")
        record.append(value)
        if len(record) > MAX_RECORD_BYTES:
            raise ValueError("complete frame contains an unreasonably large or unterminated record")
        if in_string:
            if escaped:
                escaped = False
            elif value == ord("\\"):
                escaped = True
            elif value == ord('"'):
                in_string = False
            continue
        if value == ord('"'):
            in_string = True
        elif value == ord("{"):
            stack.append(ord("}"))
        elif value == ord("["):
            stack.append(ord("]"))
        elif value in (ord("}"), ord("]")):
            if value != stack.pop():
                raise ValueError("complete frame contains mismatched JSON delimiters")
    try:
        row = json.loads(record)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError(f"complete frame contains malformed JSON: {error}") from error
    if not isinstance(row, dict):
        raise ValueError("complete frame must be a JSON array of objects")
    return row


def stream_objects(raw_path, artifact_hash):
    """Yield objects from one top-level JSON array and hash the exact bytes."""
    with raw_path.open("rb") as stream:
        reader = DigestingReader(stream)
        if reader.non_whitespace() != ord("["):
            raise ValueError("complete frame must be a JSON array of objects")
        value = reader.non_whitespace()
        if value == ord("]"):
            if reader.non_whitespace() is not None:
                raise ValueError("complete frame has content after its JSON array")
            artifact_hash.append(reader.digest)
            return
        while True:
            if value != ord("{"):
                raise ValueError("complete frame must be a JSON array of objects")
            yield read_object(reader, value)
            delimiter = reader.non_whitespace()
            if delimiter == ord("]"):
                if reader.non_whitespace() is not None:
                    raise ValueError("complete frame has content after its JSON array")
                artifact_hash.append(reader.digest)
                return
            if delimiter != ord(","):
                raise ValueError("complete frame contains malformed JSON array separators")
            value = reader.non_whitespace()
            if value is None or value == ord("]"):
                raise ValueError("complete frame contains an incomplete or trailing array element")


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

    row_count = missing = duplicates = 0
    artifact_hash = []
    # SQLite's primary-key B-tree is exact external state. Its cache is capped,
    # and temp_store=FILE prevents identifier cardinality from becoming RAM use.
    with tempfile.TemporaryDirectory(prefix="fmcsa-audit-") as workspace:
        connection = sqlite3.connect(Path(workspace) / "identifiers.sqlite3")
        try:
            connection.execute("PRAGMA journal_mode=OFF")
            connection.execute("PRAGMA synchronous=OFF")
            connection.execute("PRAGMA temp_store=FILE")
            connection.execute("PRAGMA cache_size=-4096")
            connection.execute("CREATE TABLE identifiers (dot_number TEXT PRIMARY KEY) WITHOUT ROWID")
            for row in stream_objects(raw_path, artifact_hash):
                row_count += 1
                value = row.get("dot_number")
                if value in (None, ""):
                    missing += 1
                    continue
                cursor = connection.execute(
                    "INSERT OR IGNORE INTO identifiers VALUES (?)", (str(value),)
                )
                if cursor.rowcount == 0:
                    duplicates += 1
        finally:
            connection.close()

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
    except (OSError, ValueError, json.JSONDecodeError, sqlite3.Error) as error:
        print(f"COMPLETE_FRAME_BLOCKED: {error}")
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
