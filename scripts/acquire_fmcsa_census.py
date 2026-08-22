#!/usr/bin/env python3
"""Acquire the bounded FMCSA ingestion cohort without claiming sampling."""
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

URL = "https://data.transportation.gov/resource/az4n-8mr2.json?%24limit=10000"
OUT = Path("data/raw/fmcsa/motor-carrier-census-10000.json")
META = OUT.with_suffix(".provenance.json")


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    request = Request(URL, headers={"User-Agent": "trucking-software-research/1.0"})
    with urlopen(request) as response:
        body = response.read()
    completed_utc = datetime.now(timezone.utc).isoformat()

    temporary = OUT.with_suffix(".json.tmp")
    temporary.write_bytes(body)
    temporary.replace(OUT)

    metadata = {
        "source_url": URL,
        "acquisition_completed_utc": completed_utc,
    }
    meta_temporary = META.with_suffix(".json.tmp")
    meta_temporary.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    meta_temporary.replace(META)

    print(f"wrote {len(body)} bytes to {OUT}")


if __name__ == "__main__":
    main()
