#!/usr/bin/env python3
"""Fail-closed verification of the repository's canonical FMCSA evidence package."""
import argparse
import hashlib
import json
from pathlib import Path

CONTRACT = Path("data/fmcsa/evidence-package.json")
ALLOWED_STATUSES = {
    "AVAILABLE_AND_VERIFIED", "AVAILABLE_UNVERIFIED", "RECOVERABLE", "MISSING", "NOT_REQUIRED"
}
DATASET_ID = "az4n-8mr2"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def verify(contract_path=CONTRACT, root=Path(".")):
    contract = json.loads(contract_path.read_text())
    errors = []
    if contract.get("contract_version") != "fmcsa-canonical-evidence-package-v1":
        errors.append("unsupported or missing contract version")
    if contract.get("dataset_identity", {}).get("id") != DATASET_ID:
        errors.append("contract dataset identity is not az4n-8mr2")
    artifacts = contract.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        errors.append("artifact inventory is missing")
        artifacts = []
    seen = set()
    results = []
    for artifact in artifacts:
        artifact_id = artifact.get("artifact_id")
        item_errors = []
        if not artifact_id or artifact_id in seen:
            item_errors.append("artifact ID is missing or duplicated")
        seen.add(artifact_id)
        status = artifact.get("status")
        if status not in ALLOWED_STATUSES:
            item_errors.append("inventory status is invalid")
        if artifact.get("dataset_id") != DATASET_ID:
            item_errors.append("dataset identity mismatch")
        filename = artifact.get("expected_filename")
        path = root / filename if filename else None
        present = bool(path and path.is_file())
        expected_digest = artifact.get("expected_sha256")
        expected_size = artifact.get("expected_byte_size")
        if expected_digest is not None and (not isinstance(expected_digest, str)
                                            or not expected_digest.startswith("sha256:")
                                            or len(expected_digest) != 71):
            item_errors.append("expected SHA-256 is malformed")
        if present:
            if expected_digest is None:
                item_errors.append("artifact is present but has no bound expected digest")
            elif sha256(path) != expected_digest:
                item_errors.append("SHA-256 mismatch")
            if expected_size is None:
                item_errors.append("artifact is present but has no bound expected byte size")
            elif path.stat().st_size != expected_size:
                item_errors.append("byte-size mismatch")
        elif artifact.get("required"):
            item_errors.append("required artifact is absent")
        if status == "AVAILABLE_AND_VERIFIED" and (not present or item_errors):
            item_errors.append("AVAILABLE_AND_VERIFIED claim is not supported")
        errors.extend(f"{artifact_id}: {message}" for message in item_errors)
        results.append({"artifact_id": artifact_id, "present": present,
                        "inventory_status": status, "verified": present and not item_errors,
                        "errors": item_errors})
    ready = bool(artifacts) and not errors and all(
        not artifact.get("required") or artifact.get("status") == "AVAILABLE_AND_VERIFIED"
        for artifact in artifacts
    )
    determination = ("CANONICAL_EVIDENCE_PACKAGE_BOUND" if ready
                     else "CANONICAL_EVIDENCE_PACKAGE_BLOCKED")
    if contract.get("determination") != determination:
        errors.append("declared determination does not match verified readiness")
        determination = "CANONICAL_EVIDENCE_PACKAGE_BLOCKED"
    return {"contract": str(contract_path), "dataset_id": DATASET_ID,
            "artifacts": results, "errors": errors, "determination": determination}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=CONTRACT)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    result = verify(args.contract, args.root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["determination"] != "CANONICAL_EVIDENCE_PACKAGE_BLOCKED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
