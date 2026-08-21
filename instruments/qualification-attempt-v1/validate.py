#!/usr/bin/env python3
"""Dependency-free semantic checks for qualification-attempt-v1 records."""
import json
import sys
from datetime import datetime
from pathlib import Path


CLASSIFICATIONS = {"VALID_GATE", "CANDIDATE_FALSE_GATE", "CONFIRMED_FALSE_GATE", "INDETERMINATE"}
DECISIONS = {"ALLOW", "DELAY", "REVIEW", "REJECT"}


def timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate(record):
    errors = []
    if record.get("instrument_version") != "qualification-attempt-v1":
        errors.append("instrument_version must be qualification-attempt-v1")
    decision = record.get("decision", {}).get("state")
    classification = record.get("adjudication", {}).get("classification")
    if decision not in DECISIONS:
        errors.append("invalid decision state")
    if classification not in CLASSIFICATIONS:
        errors.append("invalid classification")

    t0 = timestamp(record["t0"]["attempted_at"])
    authoritative_ids = {item["evidence_id"] for item in record["authoritative_state"]["evidence"]}
    evaluation = record["rule"]["predicate"]["t0_evaluation"]
    refs = set(evaluation["evidence_refs"])
    if classification == "CONFIRMED_FALSE_GATE":
        if decision not in {"DELAY", "REVIEW", "REJECT"}:
            errors.append("CONFIRMED_FALSE_GATE requires a restrictive decision")
        if evaluation["result"] != "SATISFIED":
            errors.append("CONFIRMED_FALSE_GATE requires predicate satisfaction at T0")
        if not refs or not refs.issubset(authoritative_ids):
            errors.append("CONFIRMED_FALSE_GATE predicate evidence must resolve to authoritative T0 evidence")
        by_id = {item["evidence_id"]: item for item in record["authoritative_state"]["evidence"]}
        if any(timestamp(by_id[ref]["as_of"]) > t0 for ref in refs if ref in by_id):
            errors.append("CONFIRMED_FALSE_GATE evidence must be effective by T0")

    previous_sequence = 0
    previous_time = t0
    for item in record.get("later_evidence", []):
        if item["sequence"] != previous_sequence + 1:
            errors.append("later evidence sequence must be contiguous and append ordered")
        observed = timestamp(item["observed_at"])
        if observed <= t0 or observed < previous_time:
            errors.append("later evidence must be observed after T0 in chronological order")
        previous_sequence, previous_time = item["sequence"], observed
    return errors


def main(argv):
    for name in argv:
        errors = validate(json.loads(Path(name).read_text()))
        if errors:
            print(f"{name}: " + "; ".join(errors), file=sys.stderr)
            return 1
        print(f"{name}: valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
