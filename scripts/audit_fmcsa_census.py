#!/usr/bin/env python3
"""Emit a deterministic, descriptive audit of an FMCSA JSON response."""
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

RAW = Path("data/raw/fmcsa/motor-carrier-census-10000.json")
OUT = Path("data/derived/fmcsa")
DATE = re.compile(r"^(?:19|20)\d\d(?:-|$)")


def kind(value):
    if value is None: return "null"
    if isinstance(value, bool): return "boolean"
    if isinstance(value, int): return "integer"
    if isinstance(value, float): return "number"
    if isinstance(value, str): return "string"
    if isinstance(value, list): return "array"
    return "object"


def main():
    raw = RAW.read_bytes()
    records = json.loads(raw)
    if not isinstance(records, list) or any(not isinstance(r, dict) for r in records):
        raise SystemExit("expected a JSON array of objects")
    fields = sorted({key for row in records for key in row})
    schema = {}
    for field in fields:
        values = [row[field] for row in records if field in row]
        nonnull = [v for v in values if v is not None]
        counts = Counter(str(v) for v in nonnull)
        years = sorted({int(str(v)[:4]) for v in nonnull if DATE.match(str(v))})
        schema[field] = {
            "observed_types": sorted({kind(v) for v in values}),
            "missing_count": len(records) - len(values),
            "null_count": sum(v is None for v in values),
            "missing_or_null_rate": round((len(records)-len(nonnull))/len(records), 6) if records else None,
            "distinct_nonnull_count": len(counts),
            "categorical_vocabulary": sorted(counts) if 0 < len(counts) <= 30 else None,
            "observed_year_range": [years[0], years[-1]] if years else None,
        }
    dots = [str(row["dot_number"]) for row in records if row.get("dot_number") not in (None, "")]
    duplicate_counts = {k: v for k, v in sorted(Counter(dots).items()) if v > 1}
    anomalies = {
        "non_object_records": 0,
        "missing_or_blank_dot_number": len(records) - len(dots),
        "duplicate_dot_number_groups": len(duplicate_counts),
        "duplicate_dot_number_rows": sum(duplicate_counts.values()),
        "duplicate_dot_numbers": duplicate_counts,
    }
    audit = {
        "row_count": len(records), "observed_field_count": len(fields),
        "observed_schema": schema, "anomalies": anomalies,
        "documentation_comparison": {
            "status": "not_assessable",
            "reason": "No versioned FMCSA Census README/data definition is present in this repository.",
            "documented_but_absent": None, "present_but_undocumented": None,
        },
    }
    provenance = {
        "source_agency": "U.S. DOT / Federal Motor Carrier Safety Administration",
        "dataset_identity": {"name": "Motor Carrier Census", "socrata_id": "az4n-8mr2"},
        "endpoint": "https://data.transportation.gov/resource/az4n-8mr2.json",
        "acquisition_query": "$limit=10000", "acquisition_completed_utc": datetime.fromtimestamp(RAW.stat().st_mtime, timezone.utc).isoformat(),
        "row_count": len(records), "raw_file": str(RAW), "sha256": hashlib.sha256(raw).hexdigest(),
        "observed_fields": fields,
        "known_limitations": ["Limit-only query has no evidenced probability-sampling semantics.", "Response has no explicit order or immutable snapshot/version.", "Ingestion/audit cohort; not representative.", "Authoritative data definition is not versioned in this repository."],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "motor-carrier-census-10000-audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True)+"\n")
    (OUT / "provenance.json").write_text(json.dumps(provenance, indent=2, sort_keys=True)+"\n")
    print(f"audited {len(records)} rows, {len(fields)} fields; sha256={provenance['sha256']}")


if __name__ == "__main__": main()
