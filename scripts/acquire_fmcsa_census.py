#!/usr/bin/env python3
"""Acquire the bounded FMCSA ingestion cohort without claiming sampling."""
from pathlib import Path
from urllib.request import Request, urlopen

URL = "https://data.transportation.gov/resource/az4n-8mr2.json?%24limit=10000"
OUT = Path("data/raw/fmcsa/motor-carrier-census-10000.json")


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    request = Request(URL, headers={"User-Agent": "trucking-software-research/1.0"})
    with urlopen(request) as response:
        body = response.read()
    temporary = OUT.with_suffix(".json.tmp")
    temporary.write_bytes(body)
    temporary.replace(OUT)
    print(f"wrote {len(body)} bytes to {OUT}")


if __name__ == "__main__":
    main()
