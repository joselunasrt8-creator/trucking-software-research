#!/usr/bin/env python3
"""Verify the preregistered MOTUS/Census alignment gate without performing a join."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parents[1]
CONTRACT = ROOT / "data/fmcsa/temporal-alignment-contract.json"


def canonical_census_audit(frame, manifest, schema):
    spec = importlib.util.spec_from_file_location("fmcsa_complete_frame_audit", ROOT / "scripts/audit_fmcsa_census.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.audit(frame, manifest, schema)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iso_epoch(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat().replace("+00:00", "Z")


def verify(contract_path=CONTRACT):
    errors, blockers, missing = [], [], []
    try:
        contract = json.loads(Path(contract_path).read_text())
    except (OSError, json.JSONDecodeError) as error:
        return {"determination": "TEMPORAL_ALIGNMENT_CONTRACT_INVALID", "errors": [str(error)], "blockers": [], "missing_paths": []}

    if contract.get("contract_version") != "fmcsa-motus-census-temporal-alignment-v1":
        errors.append("unsupported contract version")
    motus, census = contract.get("motus_input", {}), contract.get("required_census_input", {})
    if motus.get("repository_commit") != "5bef755d6fee97210cce035c21c8037668022ede":
        errors.append("MOTUS commit is not exactly bound to 5bef755")
    for role in ("frame", "manifest", "schema"):
        path = ROOT / motus.get(f"{role}_path", "")
        if not path.is_file():
            errors.append(f"MOTUS {role} is missing")
        elif sha256(path) != motus.get(f"{role}_sha256"):
            errors.append(f"MOTUS {role} digest mismatch")
    try:
        manifest = json.loads((ROOT / motus["manifest_path"]).read_text())
        if manifest.get("dataset_identity", {}).get("rows_updated_at") != motus.get("rows_updated_at"):
            errors.append("MOTUS manifest version marker mismatch")
        if manifest.get("status") != "COMPLETE_FRAME_READY_WITH_LIMITATIONS":
            errors.append("MOTUS manifest is not a complete frame")
    except (OSError, KeyError, json.JSONDecodeError):
        pass

    left, right = census.get("required_rows_updated_at"), motus.get("rows_updated_at")
    maximum = contract.get("maximum_version_marker_skew_seconds")
    if any(isinstance(value, bool) or not isinstance(value, int) for value in (left, right, maximum)):
        errors.append("version markers and maximum skew must be integers")
    else:
        skew = abs(right - left)
        computed = contract.get("computed_alignment", {})
        expected = {"reference_time_utc": iso_epoch(max(left, right)), "version_marker_skew_seconds": skew,
                    "within_preregistered_maximum": True}
        if skew > maximum or computed != expected:
            errors.append("computed temporal alignment is invalid")

    required = [ROOT / census.get(f"{role}_path", "") for role in ("frame", "manifest", "schema", "audit")]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        blockers.append("missing required Census artifacts: " + ", ".join(missing))
    else:
        try:
            census_manifest = json.loads(required[1].read_text())
            audit_result = json.loads(required[3].read_text())
            live_audit_result = canonical_census_audit(*required[:3])
            if census_manifest.get("dataset_identity", {}).get("rows_updated_at") != left:
                errors.append("Census manifest does not bind the preregistered version marker")
            if audit_result.get("status") != "COMPLETE_FRAME_READY_WITH_LIMITATIONS":
                errors.append("preserved Census audit is not successful")
            for key in ("row_count", "content_digest", "duplicate_dot_number_count", "missing_dot_number_count"):
                if audit_result.get(key) != census_manifest.get(key):
                    errors.append(f"Census audit/manifest {key} mismatch")
                if audit_result.get(key) != live_audit_result.get(key):
                    errors.append(f"preserved Census audit/canonical re-audit {key} mismatch")
            if audit_result.get("duplicate_dot_number_count") != 0 or audit_result.get("missing_dot_number_count") != 0:
                errors.append("Census identifier integrity is not admissible")
        except (OSError, ValueError, json.JSONDecodeError) as error:
            errors.append(f"Census evidence is malformed: {error}")

    if errors:
        determination = "TEMPORAL_ALIGNMENT_CONTRACT_INVALID"
    elif blockers:
        determination = "BLOCKED_EXACT_CENSUS_VERSION_UNAVAILABLE"
    else:
        determination = "TEMPORAL_ALIGNMENT_INPUTS_ADMISSIBLE_JOIN_NOT_PERFORMED"
    return {"determination": determination, "errors": errors, "blockers": blockers, "missing_paths": missing}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=CONTRACT)
    args = parser.parse_args(argv)
    result = verify(args.contract)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["determination"] == "TEMPORAL_ALIGNMENT_INPUTS_ADMISSIBLE_JOIN_NOT_PERFORMED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
